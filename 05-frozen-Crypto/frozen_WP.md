# frozen

> 赛后作品集版本：比赛提交材料（AI 对话记录、网盘链接、附件 zip MD5）留存在本地工作区，未随本文件公开。

## 题目信息

- 题目类型：Crypto（NTRU/Falcon 私钥恢复 + 冷启动内存恢复）
- 题目描述：nc 服务下发 NTRU-Falcon 公钥、一份受冷启动位翻转污染的内存镜像和加密后的 flag；附件是服务端 `task.py`。
- 附件或题目入口：`frozen_02136a685ccd425e537aa0735795019f/task.py`；比赛容器每次下发为新实例。旧实例数据 `work/banner_raw.txt`，新实例 `work/banner_new.txt`。

## 解题思路

附件直接给出了服务端全部逻辑，攻击面很明确。flag 不是被 NTRU 直接加密的，而是：

```python
canon = ",".join(str(c) for c in D).encode()
fk = hashlib.sha256(b"frozen:" + canon).digest()
ct = bytes(a ^ b for a, b in zip(flag, keystream(fk, len(flag))))
```

其中 `D = f·adj(f) + g·adj(g)`，f、g 是 σ=19.16 的 NTRU 私钥。也就是说只需要恢复 D 的 128 个整数系数，不必恢复 f、g 本身。

内存侧，`task.py` 里 `head = 8 * 128`，随后 `cblob = cblob_full[head * 8:]`，丢掉前 `head*8 = 8192` 字节，即 1024 个 float64——正好等于 `expanded_doubles` 开头写入的 fh、gh、Fh、Gh 四个 FFT 数组（4×128 实部 + 4×128 虚部）。剩下的 2304 个 double 与 `flatten_tree` 的 `nodes + leaves` 数量完全相等，说明 memory 就是 Falcon 树本身。

树根处 `G00 = |fh|² + |gh|² = FFT(D)`，所以从 Falcon 树恢复 G00，再做逆 negacyclic FFT 就能拿回 D。

## 解题过程

### 1. 解析内存布局

用 `struct`/numpy 把 memory 行解析成 2304 个 `<f8`，按 `flatten_tree` 的顺序（先所有节点，每节点 `Re(L)` 后接 `Im(L)`；最后 256 个叶子）重建结构。根 Ltop 长度 128，之后按 `_T(E)` 的递归产生长度 64、32、16、8、4、2、1 的节点。用生成函数复现这棵树的尺寸：

```python
def gen(n):
    if n == 1:
        return ("leaf",)
    m = n // 2
    return ("node", m, gen(m), gen(m))

root = ("node", 128, gen(128), gen(128))
```

节点与叶子共 2304 个 double，与抓包长度（36864 hex 字符）严格一致。块统计也吻合：前 16 块是 O(1) 的 L 值，最后两块是 1e3–1e5 量级的 Gram 叶子。

### 2. 从树的左脊重建 G00

`_T(E)` 的切分是 `Ee = 0.5*(E[:h]+E[h:])`、`O = (E[:h]-E[h:])/(2ρ)`、`L = conj(O)/Ee`。逆推得 `O = conj(L)·Ee`，于是

```python
def rebuild(Ee, L):
    m = len(L); n = 2 * m
    rho = np.exp(1j * np.pi * (2 * np.arange(m) + 1) / n)
    O = np.conj(L) * Ee
    return np.concatenate([Ee + rho * O, Ee - rho * O])
```

重建 G00 只需要 `_T(G00)` 左脊上的 7 个节点（长度 64、32、16、8、4、2、1）和第一个叶子，逐层向上即可。重建公式先用合成数据验证过（随机小整数 f、g 走同一套 fft/树代码）：G00 误差 5.8e-11，D 误差 2.7e-10。

### 3. 冷启动位翻转的修复

`corrupt_blob` 的模型：置位比特以 1%、未置位比特以 0.1% 概率翻转，只翻 bit 0–55 和符号位 63（指数高位 56–62 不翻）。

树里所有 E 都是实值回文数组（G00 与 Dright 都是实数列的谱），因此每个节点满足 `L[j] = t_j·ρ_j`（t_j 为实数），且 `t[m-1-j] = -t_j`。同一个 t 有 4 路冗余测量：

```python
vals = [L[j].real / c, L[k].real / c, L[j].imag / s, -L[k].imag / s]
# k = m-1-j, c=cos(theta), s=sin(theta), theta=pi*(2j+1)/(2m)
```

干净值在 1e-8 绝对容差内聚成一簇，翻转值成为离群点；按最大簇均值取回 t，再写回 `L[j]`、`L[k]`。实测约 20% 的复数值带可见翻转，大部分对被 3/4 投票纠正，个别双损坏对由 2/2 一致簇纠正。

### 4. 取整校验与解密

修复后重建结果：G00 虚部残差 3e-11、回文误差 5.8e-11；逆变换 `D[n] = (1/N)Σ_k G00[k]·ρ_k^{-n}` 取实部，取整误差最大 2.0e-5；`D[k] = -D[128-k]` 对所有 k 严格成立；旧实例 `D[0]=97594`（与私钥范数量级一致），`D[0:6]=[97594, 5300, -2949, 6671, -3612, 6718]`。

```python
D = [int(round(x)) for x in Dv.real]
canon = ",".join(str(c) for c in D).encode()
fk = hashlib.sha256(b"frozen:" + canon).digest()
ks = b""
ctr = 0
while len(ks) < len(ct):
    ks += hashlib.sha256(fk + ctr.to_bytes(4, "big")).digest()
    ctr += 1
flag = bytes(a ^ b for a, b in zip(ct, ks))
```

### 5. 实例 flag 变动的坑

第一次从旧容器解出 `flag{ab283317-0961-48da-a12d-afd038a57e10}`，平台报“答案错误”。再连旧地址被 ConnectionRefused，说明容器已销毁；重新下发后新实例重解，D 不同（`D[0:6]=[94922, 10961, 1187, 3651, 6394, -1339]`），flag 也不同。确认 `flag` 随容器部署重新生成，旧实例结果无效，最终以新容器结果提交。

## 复现脚本

- `work/solve.py`：主解算脚本（`python solve.py banner_new.txt`）
- `work/capture_solve.py`：连接容器抓 banner 并直接解算（`python capture_solve.py <host> <port>`）
- 输入：`work/banner_raw.txt`（旧实例）、`work/banner_new.txt`（新实例）
- 运行日志：`work/solve_old.log`、`work/solve_new.log`
- 依赖：Python 3.13 + numpy；不需要 fpylll 或格约减，因为只做树重建、不恢复 f、g

`work/solve.py` 全文：

```python
#!/usr/bin/env python3
"""frozen solver: cold-boot Falcon tree -> G00 -> D -> keystream -> flag."""
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
    if m == 1:          # 实回文 E 长度为 2 时 L = t*i, t=0
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


E = np.array([d[leaf_pos[0]]], dtype=complex)
for i in range(7, 0, -1):
    E = rebuild(E, clean_L(getL(i)))

rho_full = np.exp(1j * np.pi * (2 * np.arange(N) + 1) / N)
A = np.power(rho_full[None, :], -np.arange(N)[:, None])
Dv = (A @ E) / N
D = [int(round(x)) for x in Dv.real]
assert max(abs(Dv.real - np.round(Dv.real))) < 1e-3
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
```

## Flag

`flag{c6f55121-2fb2-494d-b7a6-8dffd4871e1b}`

来源：新容器 39.105.87.43:26626 的 banner（`work/banner_new.txt`）解密结果。旧实例结果为 `flag{ab283317-0961-48da-a12d-afd038a57e10}`，已被平台判错。

验证状态：已获取；平台提交通过（100 分）。
