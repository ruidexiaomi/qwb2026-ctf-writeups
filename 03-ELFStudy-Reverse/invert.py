import struct
import sys

M = (1 << 64) - 1
C = 0x9E3779B97F4A7C15


def q(page, addr):
    return struct.unpack_from("<Q", page, addr - 0x7000)[0]


def rol(x, n):
    return ((x << n) | (x >> (64 - n))) & M


def ror(x, n):
    return ((x >> n) | (x << (64 - n))) & M


def round_fn(x, k):
    t = rol((x + k) & M, 13)
    s = rol(x, 29)
    u = t ^ s
    return (u + rol(x, 47)) & M


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "rxpage.bin"
    page = open(path, "rb").read()
    if len(page) != 0x1000:
        raise SystemExit("expect 4096-byte RX page dump")

    # 0x739a 处的解密函数使用的常量
    k1 = q(page, 0x7686) ^ q(page, 0x768E)
    k2 = q(page, 0x7696) ^ q(page, 0x769E)
    t1 = q(page, 0x76A6)
    t2 = q(page, 0x76AE)

    # 由固定常量生成 30 个轮密钥 w[4..33]
    w = [0] * 34
    w[2], w[3] = k1, k2
    r = (2 * C) & M
    for i in range(2, 32):
        a, b = w[i + 1], w[i]
        w[i + 2] = (rol((a + b) & M, 13) ^ ror(b, 7) ^ r) & M
        r = (r + C) & M

    # 逆向 30 轮 Feistel
    r8, r9 = t1, t2
    for i in range(31, 1, -1):
        r8, r9 = (r9 ^ round_fn(r8, w[i + 2])) & M, r8

    raw = struct.pack("<QQ", r8 ^ k1, r9 ^ k2)
    print("raw :", raw.hex())
    print("FLAG: flag{%s}" % raw.hex())


if __name__ == "__main__":
    main()
