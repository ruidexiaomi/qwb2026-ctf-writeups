import struct

M = (1 << 64) - 1
C = 0x9E3779B97F4A7C15
SRC = "elfstudy"

d = open(SRC, "rb").read()

# 1) 页面尾部 0x1988 处的隐藏重定位表，每条 Elf64_Rela 24 字节。
#    14 条 (type=1, sym=0x39, r_offset=0x7325..0x738d) 写出的值是 stub，
#    记录 0 (type=SIZE64, sym=0) 的 addend 恰好是符号 0x39 的值 K。
recs = [struct.unpack_from("<QQQ", d, 0x1988 + 24 * i) for i in range(69)]
K = recs[0][2]

stub = bytearray(0x70)
for roff, info, addend in recs:
    if 0x7325 <= roff <= 0x7394 and (info & 0xFFFFFFFF) == 1 and (info >> 32) == 0x39:
        o = roff - 0x7325
        stub[o:o + 8] = struct.pack("<Q", (addend + K) & M)
assert stub[:2] == b"\x53\x48"

# 2) stub 在加载期对 0x7396..0x76c5 做从高到低的滚动 XOR/累加解密。
code = bytearray(d[0x7396:0x76C6])
key = 0
for i in range(0xCB, 0, -1):
    off = i * 4
    c = struct.unpack_from("<I", code, off)[0]
    p = c ^ key
    struct.pack_into("<I", code, off, p)
    if p == 0:  # 遇到 0 双字提前结束
        break
    key = (key + p) & 0xFFFFFFFF

page = bytearray(0x1000)
page[0x325:0x395] = stub
page[0x396:0x6C6] = code
assert b"flag accepted" in page and b"/proc/self/status" in page

open("stub_reconstructed.bin", "wb").write(bytes(stub))
open("hidden_func_decrypted.bin", "wb").write(bytes(code))

# 3) 校验器：固定轮密钥 + 30 轮 Feistel，目标值 16 字节；逆向得到 flag 输入。
def q(addr):
    return struct.unpack_from("<Q", page, addr - 0x7000)[0]

k1 = q(0x7686) ^ q(0x768E)
k2 = q(0x7696) ^ q(0x769E)
t1 = q(0x76A6)
t2 = q(0x76AE)

def rol(x, n):
    return ((x << n) | (x >> (64 - n))) & M

def ror(x, n):
    return ((x >> n) | (x << (64 - n))) & M

w = [0] * 34
w[2], w[3] = k1, k2
r = (2 * C) & M
for i in range(2, 32):
    w[i + 2] = (rol((w[i + 1] + w[i]) & M, 13) ^ ror(w[i], 7) ^ r) & M
    r = (r + C) & M

def f(x, k):
    return ((rol((x + k) & M, 13) ^ rol(x, 29)) + rol(x, 47)) & M

r8, r9 = t1, t2
for i in range(31, 1, -1):
    r8, r9 = (r9 ^ f(r8, w[i + 2])) & M, r8

raw = struct.pack("<QQ", r8 ^ k1, r9 ^ k2)
flag = "flag{" + raw.hex() + "}"
print(flag)
