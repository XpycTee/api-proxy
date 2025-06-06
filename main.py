import ssl
import certifi
from flask import Flask, request, Response
import urllib.request
import urllib.parse

app = Flask(__name__)

BYBIT_API_BASE = 'https://api.bybit.com'

@app.route('/bybit/<path:endpoint>', methods=['GET', 'POST'])
def proxy_to_bybit(endpoint):
    url = f"{BYBIT_API_BASE}/{endpoint}"
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

        return Response(content, status, response_headers)
    except Exception as e:
        return Response(f"Ошибка при обращении к Bybit API: {e}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
