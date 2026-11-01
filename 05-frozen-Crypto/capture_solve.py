#!/usr/bin/env python3
"""Capture a fresh frozen banner from the challenge container and solve it.

usage: python capture_solve.py <host> <port>
"""
import socket, sys, time, subprocess, os

host = sys.argv[1]
port = int(sys.argv[2])
out = "banner_new.txt"

print(f"connecting to {host}:{port} ...")
s = socket.create_connection((host, port), timeout=20)
s.settimeout(180)
data = b""
t0 = time.time()
while True:
    try:
        chunk = s.recv(65536)
    except socket.timeout:
        print("read timeout")
        break
    if not chunk:
        break
    data += chunk
    if data.count(b"\n") >= 3:
        break
s.close()
print(f"got {len(data)} bytes in {time.time()-t0:.1f}s")
open(out, "wb").write(data)

here = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, os.path.join(here, "solve.py"), os.path.join(here, out)], check=True)
