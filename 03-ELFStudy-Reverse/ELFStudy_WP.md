# ELFStudy

## 题目信息

- 题目类型：Reverse
- 题目描述：附件下载（题目窗口无额外文字）
- 附件或题目入口：`elfstudy_401568f195e6e6e12923a6b9687d14b5.zip`，解压得到 `elfstudy`（ELF64 PIE、stripped，43,304 字节，SHA-256 `c1c00a784b992dbeec4e96b4af69e2aa8a7a9b40b72b1069995e759259abe2b4`）

## 解题思路

程序 `elfstudy` 是个 ELF 结构查看器：把目标文件读进 64 KiB 缓冲区，打印 ELF header、program headers 和 sections。`main` 路径里没有输入校验，字符串里也找不到 flag，直接逆主逻辑没有收获。

真正的线索在两处 LOAD 段尾的页间隙（page slack）。第一处是第一个 R LOAD：`p_filesz` 结束在 `0x1988`，但按页映射会一直映射到 `0x2000`，`0x1988-0x1FFF` 没有 section 覆盖。第二处是 RX LOAD：`p_filesz` 结束在 `0x7325`，页映射到 `0x8000`，`0x7325-0x7FFF` 同样没有 section 覆盖。这两段在文件里都不是全零：前者是 22 条 24 字节记录，形态就是 `Elf64_Rela`；后者在 `0x76C6` 处有一份完整的 `.rela.plt` 副本，前面从 `0x7395` 起是一段高熵数据。

隐藏 Rela 表里第 12 条 `(0x3b34, 0x21, 0x9090c300003861e8)` 正好对应 `sub_3B30` 中被 NOP 掉的 8 个字节：原始内容应为 `e8 61 38 00 00 c3 90 90`，也就是 `call 0x739a; ret`。出题人把对隐藏函数的调用抹掉了，恢复方法留在了页间隙里。

只恢复这个 call 再运行，程序不崩、退出码为 0，说明 `0x739a` 处确实有可执行内容。用 ptrace 在加载完成后 dump RX 段最后一页，`0x739a` 处出现了一段文件里不存在的完整函数，包含 `/proc/self/status`、`TracerPid:`、`flag accepted` 等字符串；隐藏校验器是在加载期被动态解出来的。

继续追解密过程：在 `0x7325` 下硬件写断点，抓到加载器先写入一段临时 stub；stub 做反调试检查后，对 `0x7396-0x76C5` 从高地址向低地址做“滚动 XOR + 累加”解密，把校验器解出来；随后恢复 `0x3b34` 的 call，最后用 `rep stosb` 把自己清掉。

这段 stub 也能纯静态还原：隐藏表里 14 条 `(type=1, sym=0x39, r_offset=0x7325..0x738d)` 的 addend 加上常量 K 就是 stub 的 14 个 qword，K 恰好是记录 0（`SIZE64`，sym=0）的 addend `0x16493f2103392e07`。按这个关系重建 stub，再按 stub 的算法解密，结果与运行时 dump 的页逐字节一致。

校验器的逻辑是：先确认 `r_debug->r_brk` 没被下 `0xCC` 断点、`/proc/self/status` 的 `TracerPid` 为 0；再检查 `dest`（即 `argv[1]`）是 38 字节的 `flag{32位hex}`；把 32 个 hex 解成 16 字节，用固定轮密钥的 30 轮 Feistel 变换成 16 字节，与硬编码目标比较，命中就 `write(1, "flag accepted\n", 14)`。Feistel 是可逆的，直接用目标值反向跑 30 轮就能还原输入。

## 解题过程

### 1. 确认程序行为

```text
$ file elfstudy
elfstudy: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV),
dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2,
BuildID[sha1]=e9e5c048fa11349c8486d9944e2c5ad0f4256f8a,
for GNU/Linux 3.2.0, stripped

$ ./elfstudy elfstudy
ELFStudy 1.4.2 — ELF structure inspector
[image] 43304 bytes loaded
[header] ...
[program headers] 14 entries
[sections] 31 entries
[symbols] summary unavailable without a section-name table in this build
```

`strings` 里没有 flag，IDA 里 `main` 和 `sub_4080` 只负责解析/打印结构。程序本身不是校验器。

### 2. 两处页尾数据

第一个 LOAD 的 `p_filesz=0x1988`，RX LOAD 的 `p_filesz=0x5325`（起始 `0x2000`，结束 `0x7325`）。页对齐映射使两段页尾仍能访问：

- `0x1988-0x1FFF`：22 条 24 字节记录，解析为 `Elf64_Rela`；
- `0x7325-0x7FFF`：`0x7325-0x7394` 是 112 字节零区，`0x7395` 起 817 字节高熵数据，`0x76C6` 起是 `.rela.plt` 的完整副本。

隐藏表里第 12 条记录：

```text
record12: off=0x3b34 info=0x21 bytes=e861380000c39090
```

对应 `sub_3B30` 当前的内容 `endbr64; 90*8; ret`：恢复后应变成 `endbr64; call 0x739a; ret; nop; nop`。

### 3. 运行时页被解密

只把记录 12 写回，运行 `elfstudy_restored elfstudy`，程序正常打印完结构并返回 0。说明 `0x739a` 处并不是乱码，而是加载期被解出来的代码。

用 `solve/dump_page.c` 在加载完成后（硬件断点停在 `sub_3B30` 入口，`AT_ENTRY - 0x2e90` 计算 PIE 基址）dump RX 最后一页：

```text
base=0x55707f199000 dumped RX page -> rxpage_test.bin
```

`rxpage.bin` 的 `0x739a` 处出现：

```text
739a: f3 0f 1e fa          endbr64
739e: 53                   push rbx
739f: 55                   push rbp
73a0: 41 54                push r12
73a2: 48 89 e5             mov rbp,rsp
73a5: 48 8d 1d ea ff ff ff lea rbx,[rip-0x16]
...
```

页内字符串包括 `/proc/self/status`、`TracerPid:`、`flag accepted`。这些内容在文件里都不存在，确认是加载期写入。

### 4. 抓临时 stub

在 `0x7325` 下硬件写断点，第一次写入的字节为 `0x53`（`push rbx`），写入发生在主程序之外的加载器代码中（`ld.so` 侧的一次 memcpy），随后 `0x7325` 处出现完整 stub。stub 的关键反汇编：

```text
7325: 53                   push   rbx
7326: 48 8d 1d f8 ff ff ff lea    rbx,[rip-0x8]          ; rbx = 0x7325
732d: 48 8d 05 01 00 00 00 lea    rax,[rip+0x1]
7334: 48 25 00 f0 ff ff    and    rax,0xfffffffffffff000
733a: 48 05 60 3d 00 00    add    rax,0x3d60             ; DT_DEBUG
7340: 48 8b 00             mov    rax,[rax]
7343: 48 85 c0             test   rax,rax
7346: 74 3b                je     0x7383
7348: 48 8b 48 10          mov    rcx,[rax+0x10]         ; r_debug->r_brk
734c: 48 85 c9             test   rcx,rcx
734f: 74 32                je     0x7383
7351: 80 39 cc             cmp    byte [rcx],0xcc        ; 是否被下断点
7354: 74 2d                je     0x7383
7356: 48 8d bb 71 00 00 00 lea    rdi,[rbx+0x71]         ; 0x7396
735d: b9 cb 00 00 00       mov    ecx,0xcb
7362: 31 c0                xor    eax,eax
7364: 31 04 8f             xor    [rdi+rcx*4],eax        ; 解密
7367: 74 1a                je     0x7383
7369: 03 04 8f             add    eax,[rdi+rcx*4]
736c: e2 f6                loop   0x7364
736e: 48 8d 83 0f c8 ff ff lea    rax,[rbx-0x37f1]       ; 0x3b34
7375: c6 00 e8             mov    byte [rax],0xe8
7378: c7 40 01 61 38 00 00 mov    dword [rax+1],0x3861   ; call 0x739a
737f: c6 40 05 c3          mov    byte [rax+5],0xc3       ; ret
7383: 53                   push   rbx
7384: 5f                   pop    rdi
7385: 6a 61                push   0x61
7387: 59                   pop    rcx
7388: 31 c0                xor    eax,eax
738a: 5b                   pop    rbx
738b: f3 aa                rep stos byte [rdi],al           ; 擦除 stub
738d: c3                   ret
```

也就是说，加载期先放一个临时 stub，它做反调试、解密页尾、恢复对 `0x739a` 的调用，然后擦掉自己，运行期只留下校验器。

### 5. 静态重建 stub 与解密

隐藏表里 14 条 `(type=1, sym=0x39, r_offset=0x7325..0x738d)` 的 addend 与 stub 的 14 个 qword 只差一个常量 K；K 正好是记录 0（`SIZE64`，sym=0，r_offset=0x958）的 addend：

```text
K = 0x16493f2103392e07
stub_qword[i] = record_addend[i] + K   (mod 2^64)
```

用这个关系重建的 stub 与运行时抓到的 stub 完全一致。再按 stub 的算法，从 `0x76C2` 向低地址处理 203 个 dword：

```text
key = 0
for i = 0xcb .. 1:
    p = dword[i] ^ key
    dword[i] = p
    if p == 0: break
    key = (key + p) & 0xffffffff
```

静态解密结果与运行时页逐字节一致：

```text
stub matches runtime stub: True
decrypted matches runtime: True
```

### 6. 反推 Feistel

解密出的校验器在 `0x74e5` 起把 32 个 hex 解成 16 字节；`0x7537` 起初始化两个 64 位常量并生成 30 个轮密钥：

```text
k1 = 0x1fa6bee7224fb586
k2 = 0x56fc5596cf5bad58
T1 = 0x4fb335a84fa7d2d7   ; 0x76a6
T2 = 0x02a183e3b4f4f49f   ; 0x76ae
C  = 0x9e3779b97f4a7c15
```

第二轮循环是 30 轮 Feistel，每轮：

```text
F(x, k) = (rol(x + k, 13) ^ rol(x, 29)) + rol(x, 47)
(r8, r9) = (r9, r8 ^ F(r9, k))
```

初始状态 `(r8, r9) = (w0 ^ k1, w1 ^ k2)`，轮密钥由固定常量生成，与输入无关，所以整个变换可逆。用 `T1/T2` 反向跑 30 轮，得到：

```text
raw : 4865f2079724968a95c217e0ff4db6c6
FLAG: flag{4865f2079724968a95c217e0ff4db6c6}
```

### 7. 动态验证

```text
$ python3 restore_call.py
record12: off=0x3b34 info=0x21 bytes=e861380000c39090
written elfstudy_restored

$ ./elfstudy_restored 'flag{4865f2079724968a95c217e0ff4db6c6}'
ELFStudy: cannot open 'flag{4865f2079724968a95c217e0ff4db6c6}'
...
[header] truncated: need at least 64 bytes for an ELF64 header
flag accepted
```

错误 flag（`flag{000...0}`）不会输出 `flag accepted`。校验器带反调试，动态验证要在没有 ptrace 的正常环境运行。

## 复现脚本

- `solve/solve.py`：纯静态一键解，读入 `elfstudy`，从隐藏 Rela 表重建 stub、解密页尾、反推 Feistel，打印 flag。
- `solve/restore_call.py`：把记录 12 写回 `0x3b34`，生成 `elfstudy_restored`，用于动态验证。
- `solve/dump_page.c`：可选，ptrace 在加载完成后 dump RX 页（`rxpage.bin`），用于对照静态结果。
- `solve/invert.py`：可选，从 `rxpage.bin` 反推（`solve.py` 已合并该逻辑）。

```bash
cd solve
python3 solve.py
# flag{4865f2079724968a95c217e0ff4db6c6}

python3 restore_call.py
./elfstudy_restored 'flag{4865f2079724968a95c217e0ff4db6c6}'
# flag accepted
```

`solve.py` 的核心：

```python
import struct

M = (1 << 64) - 1
C = 0x9E3779B97F4A7C15
d = open("elfstudy", "rb").read()

recs = [struct.unpack_from("<QQQ", d, 0x1988 + 24 * i) for i in range(69)]
K = recs[0][2]  # 记录 0（SIZE64, sym=0）的 addend，即符号 0x39 的值

stub = bytearray(0x70)
for roff, info, addend in recs:
    if 0x7325 <= roff <= 0x7394 and (info & 0xFFFFFFFF) == 1 and (info >> 32) == 0x39:
        o = roff - 0x7325
        stub[o:o + 8] = struct.pack("<Q", (addend + K) & M)

code = bytearray(d[0x7396:0x76C6])
key = 0
for i in range(0xCB, 0, -1):
    off = i * 4
    c = struct.unpack_from("<I", code, off)[0]
    p = c ^ key
    struct.pack_into("<I", code, off, p)
    if p == 0:
        break
    key = (key + p) & 0xFFFFFFFF

page = bytearray(0x1000)
page[0x325:0x395] = stub
page[0x396:0x6C6] = code

def q(addr):
    return struct.unpack_from("<Q", page, addr - 0x7000)[0]

def rol(x, n):
    return ((x << n) | (x >> (64 - n))) & M

def ror(x, n):
    return ((x >> n) | (x << (64 - n))) & M

k1 = q(0x7686) ^ q(0x768E)
k2 = q(0x7696) ^ q(0x769E)
t1, t2 = q(0x76A6), q(0x76AE)

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
print("flag{" + raw.hex() + "}")
```

依赖：Python 3（仅标准库）。动态验证需要 Linux x86-64；`dump_page.c` 需要 gcc。

## Flag

`flag{4865f2079724968a95c217e0ff4db6c6}`

来源：静态重建加载期 stub、解密隐藏校验器后，对 30 轮 Feistel 反向计算得到 16 字节输入，hex 编码为 32 位 flag 主体。

验证状态：已获取；平台提交通过（100 分）。本机用恢复调用后的 `elfstudy_restored` 动态运行，输出 `flag accepted`，错误 flag 无输出。
