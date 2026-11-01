#!/usr/bin/env python3
"""frozen solver: cold-boot Falcon tree -> G00 -> D -> keystream -> flag.

Recovers D = f*adj(f) + g*adj(g) from the corrupted memory dump.
The dump is the Falcon tree (task.py trims the four FFT arrays via head=8*128).
G00 = |fh|^2+|gh|^2 = FFT(D), and G00 is the E-array at the root of _T(G00),
reconstructible from the left spine of that subtree.

Every node L satisfies L[j] = t_j*rho_j (t_j real), t[m-1-j] = -t_j,
so each value is measured 4x redundantly; tight-cluster voting removes the
cold-boot bit flips.
"""
import json, math, hashlib, sys
import numpy as np

PATH = sys.argv[1] if len(sys.argv) > 1 else "banner_raw.txt"

txt = open(PATH, "rb").read().decode()
lines = txt.split("\n")
pk = json.loads(lines[0].split("=", 1)[1].strip())
N = pk["N"]
mem = bytes.fromhex(lines[1].split("=", 1)[1].strip())
ct = bytes.fromhex(lines[2].split("=", 1)[1].strip())
d = np.frombuffer(mem, dtype="<f8").copy()


def gen(n):
    if n == 1:
        return ("leaf",)
    m = n // 2
    return ("node", m, gen(m), gen(m))


root = ("node", 128, gen(128), gen(128))
order = []


def walk(t):
    if t[0] == "leaf":
        order.append(("leaf",))
        return
    order.append(("node", t[1]))
    walk(t[2])
    walk(t[3])


walk(root)

node_pos = []
p = 0
for it in order:
    if it[0] == "node":
        node_pos.append((it[1], p))
        p += 2 * it[1]
leaf_pos = []
for it in order:
    if it[0] == "leaf":
        leaf_pos.append(p)
        p += 1
assert p == len(d)


def getL(idx):
    m, off = node_pos[idx]
    return d[off:off + m] + 1j * d[off + m:off + 2 * m]


TOL = 1e-8


def clean_L(L):
    m = len(L)
    if m == 1:          # L = t*i with t = 0 for a real palindromic E of length 2
        return np.zeros(1, dtype=complex)
    out = np.empty(m, dtype=complex)
    for j in range(m // 2):
        k = m - 1 - j
        th = math.pi * (2 * j + 1) / (2 * m)
        c, s = math.cos(th), math.sin(th)
        vals = []
        if abs(c) > 1e-8:
            vals += [L[j].real / c, L[k].real / c]
        if abs(s) > 1e-8:
            vals += [L[j].imag / s, -L[k].imag / s]
        vals = np.sort(np.array(vals))
        groups, cur = [], [vals[0]]
        for v in vals[1:]:
            if abs(v - cur[-1]) <= TOL:
                cur.append(v)
            else:
                groups.append(cur)
                cur = [v]
        groups.append(cur)
        groups.sort(key=len, reverse=True)
        t = float(np.mean(groups[0]))
        out[j] = t * complex(c, s)
        out[k] = t * complex(c, -s)
    return out


def rebuild(Ee, L):
    m = len(L)
    n = 2 * m
    rho = np.exp(1j * np.pi * (2 * np.arange(m) + 1) / n)
    O = np.conj(L) * Ee
    return np.concatenate([Ee + rho * O, Ee - rho * O])


# climb the left spine node7..node1, starting from the first leaf
E = np.array([d[leaf_pos[0]]], dtype=complex)
for i in range(7, 0, -1):
    E = rebuild(E, clean_L(getL(i)))

# G00 is Hermitian; D = (1/N) sum_k G00[k] * rho_k^{-n}
rho_full = np.exp(1j * np.pi * (2 * np.arange(N) + 1) / N)
A = np.power(rho_full[None, :], -np.arange(N)[:, None])
Dv = (A @ E) / N
D = [int(round(x)) for x in Dv.real]
err = float(np.max(np.abs(Dv.real - np.round(Dv.real))))
print(f"[diag] G00 imag_max={np.max(np.abs(E.imag)):.2e} "
      f"palin_err={np.max(np.abs(E.real - E.real[::-1])):.2e}", file=sys.stderr)
print(f"[diag] D[0:6]={D[:6]} max_round_err={err:.2e}", file=sys.stderr)
print(f"[diag] D[1:] antisymmetric={all(D[k] == -D[N - k] for k in range(1, N))}", file=sys.stderr)
assert err < 1e-3
assert all(D[k] == -D[N - k] for k in range(1, N))

canon = ",".join(str(c) for c in D).encode()
fk = hashlib.sha256(b"frozen:" + canon).digest()
ks = b""
ctr = 0
while len(ks) < len(ct):
    ks += hashlib.sha256(fk + ctr.to_bytes(4, "big")).digest()
    ctr += 1
flag = bytes(a ^ b for a, b in zip(ct, ks))
print(flag.decode())
