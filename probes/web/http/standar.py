import urlparse
import httplib

def httping(host, report, url=None, method='GET', timeout=30):
    """ """
    if url is None:
        url = 'http://%s:80' % host.ip

    urlp = urlparse.urlparse(url)

    if urlp.scheme == 'http':
        conn = httplib.HTTPConnection(urlp.netloc, timeout=timeout)
    elif urlp.scheme == 'https':
        conn = httplib.HTTPSConnection(urlp.netloc, timeout=timeout)

    timer = report.create_timer("request time").start()
    conn.request(method=method, url=urlp.path)
    timer.stop()
