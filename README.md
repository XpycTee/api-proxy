# Simple APIProxy

## To run APIProxy:

```bash
docker run -d \
    --name=apiproxy \
    -v=apiproxy_config:/app/config \
    -p=8080:8080 \
    xpyctee/apiproxy
```

## Configuration (`/app/config/config.yaml`):

```yaml
urls:
  steam: # Prefix
    url: 'https://steamcommunity.com' # Base redirect url
    rate_limit: 30  # (Optional) Queries per minute
```

## Example Request:
`http://127.0.0.1:8080/PREFIX/....`

```bash
STAEMID=12345678....

curl 'http://127.0.0.1:8080/steam/inventory/$STEAMID/730/2?l=english&count=100'
```

> This redirects to `https://steamcommunity.com/inventory/$STEAMID/730/2?l=english&count=100`, proxying the request with headers and query arguments using GET or POST.

[DockerHub](https://hub.docker.com/r/xpyctee/apiproxy)