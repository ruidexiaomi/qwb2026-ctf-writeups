import struct

# 隐藏重定位表在 0x1988，每条 24 字节 (r_offset, r_info, r_addend)
# 第 12 条记录给出被抹掉的 call 指令：0x3b34 <- e8 61 38 00 00 c3 90 90
src = "elfstudy"
dst = "elfstudy_restored"
d = bytearray(open(src, "rb").read())
off, info, val = struct.unpack_from("<QQQ", d, 0x1988 + 12 * 24)
print(f"record12: off={off:#x} info={info:#x} bytes={struct.pack('<Q', val).hex()}")
d[off:off + 8] = struct.pack("<Q", val)
open(dst, "wb").write(d)
print(f"written {dst}")
