import ssl
import time
import certifi
import urllib.request
import urllib.parse
import yaml

from datetime import datetime

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
    context = ssl.create_default_context(cafile=certifi.where())
    
    try:
        if request.method == 'GET':
            full_url = url + '?' + urllib.parse.urlencode(request.args)
            app.logger.debug(full_url)
            req = urllib.request.Request(full_url, headers=headers, method='GET')
            with urllib.request.urlopen(req, context=context) as resp:
                content = resp.read()
                status = resp.status
                response_headers = [(k, v) for k, v in resp.getheaders()
                                   if k.lower() not in ['content-length', 'transfer-encoding', 'connection']]
        elif request.method == 'POST':
            data = request.get_data()
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, context=context) as resp:
                content = resp.read()
                status = resp.status
                response_headers = [(k, v) for k, v in resp.getheaders()
                                   if k.lower() not in ['content-length', 'transfer-encoding', 'connection']]
        else:
            return Response("Метод не поддерживается", status=405)
        app.logger.debug(content)
        app.logger.debug(status)
        app.logger.debug(resp.getheaders())
        return Response(content, status, response_headers)
    except Exception as e:
        return Response(f"Ошибка при обращении к API: {e}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
