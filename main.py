import time
import yaml

import httpx

from datetime import datetime
from urllib.parse import urlencode

from flask import Flask, request, Response
from flask_caching import Cache

cache = Cache()
app = Flask(__name__)
app.config['CACHE_TYPE'] = 'MemcachedCache'
app.config['CACHE_MEMCACHED_SERVERS'] = ['127.0.0.1:11211']
cache.init_app(app)


def get_urls():
    with open('config/config.yaml', "r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file).get('urls', {})


@app.route('/<prefix>/<path:endpoint>', methods=['GET', 'POST'])
def proxy(prefix, endpoint):
    urls = get_urls()
    url_info = urls.get(prefix)
    if not url_info or 'url' not in url_info:
        return Response("Unknown prefix", status=404)
    base_url = url_info['url']
    rate_limit = url_info.get('rate_limit')

    if rate_limit:
        # Время между запросами в секундах
        query_delay_sec = 60.0 / rate_limit

        now = datetime.now()
        last = cache.get(f'last_{prefix}')

        if last is not None:
            elapsed = (now - last).total_seconds()
            wait = query_delay_sec - elapsed
            if wait > 0:
                time.sleep(wait)
        cache.set(f'last_{prefix}', datetime.now(), timeout=query_delay_sec)

    url = f"{base_url}/{endpoint}"
    headers = {key: value for key, value in request.headers if key != 'Host'}
    
    try:
        with httpx.Client(headers=headers) as client:
            if request.method == 'GET':
                response = client.get(url, params=request.args)
            elif request.method == 'POST':
                data = request.get_data()
                response = client.post(url, data=data)
            else:
                return Response("Метод не поддерживается", status=405)
            
            response.raise_for_status()
            content = response.read()
            status = response.status_code
            response_headers = [(k, v) for k, v in response.headers.items() if k.lower() not in ['content-length', 'transfer-encoding', 'connection']]
        app.logger.debug(content)
        app.logger.debug(status)
        app.logger.debug(response.headers)
        return Response(content, status, response_headers)
    except Exception as e:
        return Response(f"Ошибка при обращении к API: {e}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
