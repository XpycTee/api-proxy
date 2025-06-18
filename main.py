import datetime
import ssl
import time
import certifi
from flask import Flask, request, Response
import urllib.request
import urllib.parse
import yaml

app = Flask(__name__)

# где-то в модуле, например, в app.config или глобальном dict:
LAST_REQUESTS = {}

def get_urls():
    with open('config.yaml', "r", encoding="utf-8") as config_file:
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
        last = LAST_REQUESTS.get(prefix)

        if last is not None:
            elapsed = (now - last).total_seconds()
            wait = query_delay_sec - elapsed
            if wait > 0:
                time.sleep(wait)

    url = f"{base_url}/{endpoint}"
    headers = {key: value for key, value in request.headers if key != 'Host'}
    context = ssl.create_default_context(cafile=certifi.where())
    
    try:
        if request.method == 'GET':
            full_url = url + '?' + urllib.parse.urlencode(request.args)
            req = urllib.request.Request(full_url, headers=headers, method='GET')
            with urllib.request.urlopen(req, context=context) as resp:
                content = resp.read()
                status = resp.status
                response_headers = [(k, v) for k, v in resp.getheaders()
                                   if k.lower() not in ['content-encoding', 'content-length', 'transfer-encoding', 'connection']]
        elif request.method == 'POST':
            data = request.get_data()
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, context=context) as resp:
                content = resp.read()
                status = resp.status
                response_headers = [(k, v) for k, v in resp.getheaders()
                                   if k.lower() not in ['content-encoding', 'content-length', 'transfer-encoding', 'connection']]
        else:
            return Response("Метод не поддерживается", status=405)
        LAST_REQUESTS[prefix] = datetime.now()
        return Response(content, status, response_headers)
    except Exception as e:
        return Response(f"Ошибка при обращении к Bybit API: {e}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
