# 第十届“强网杯”全国网络安全挑战赛 解题作品集

- 队伍：404NotFound
- 成绩：600 分，全国第 911 名，6 题全解，0 一血
- 方向分布：Web×3、Pwn×1、Reverse×1、Crypto×1
- 收录：5 篇赛后 Writeup + 核心利用/分析脚本，可按各题 WP 复现

> 说明：vaultlink（Web）为官方环境问题统一补偿，其非预期解在环境维护后已失效，未计入本作品集的技术复盘。其余 5 题均为自主解出并通过平台验证。

## 目录

| 编号 | 题目 | 方向 | 核心技术 | 平台验证 |
|---|---|---|---|---|
| 01 | cwp | Web | 批量接口索引错位 → SQL 注入 → 缓存污染 → 权限提升 → 本机服务提权 | 通过（100） |
| 02 | easytl | Pwn | TLS 1.3 PSK 手工握手 → 长度错配 → SNI 栈溢出 → canary 爆破 → 两段 ROP | 通过（100） |
| 03 | ELFStudy | Reverse | ELF 页尾 slack → 隐藏 Rela 表 → 加载期 stub 重建 → Feistel 逆运算 | 通过（100） |
| 04 | ezphp | Web | SSRF → Redis EVAL → PHP 会话反序列化 → 配置自动 include RCE | 通过（100，队友提交） |
| 05 | frozen | Crypto | Falcon 树重建 → G00 → 逆 FFT → 位翻转投票纠错 → 解密 | 通过（100） |

## 脚本清单

### 01 cwp（Web）

| 文件 | 用途 | 依赖 | 运行 |
|---|---|---|---|
| `exploit.py` | 完整利用链：bulk 索引错位 → 嵌套批量 → raw `omit` SQL 注入 → `ROW_CACHE` 污染 → staff 权限 → `skin-editor` Webshell → hpxd vault 绕过 + `files/list` 命令注入 | Python 3、`requests` | 修改脚本顶部 `TARGET` 后执行 `python exploit.py` |

### 02 easytl（Pwn）

| 文件 | 用途 | 依赖 | 运行 |
|---|---|---|---|
| `easytl_exploit.py` | 可导入模块：构造 TLS 1.3 PSK ClientHello/binder，利用 identity 长度错配与 SNI 栈溢出，提供 canary 爆破与两段 ROP | Python 3 标准库 | 按 WP 方式导入，例如 `import easytl_exploit as e; e.brute_canary(server="<host>")` |
| `remote_pwn.sh` | 远端执行封装，默认尝试读取 `/root/flag.txt`、`/flag`、`/home/*/flag*` | Python 3、`easytl_exploit.py` | `sh remote_pwn.sh <canary_hex> 4`；需把模块放到可导入路径，并把脚本内的远端地址换成新靶机 |

### 03 ELFStudy（Reverse）

| 文件 | 用途 | 依赖 | 运行 |
|---|---|---|---|
| `solve.py` | 纯静态解：从页尾隐藏 Rela 表重建加载期 stub，解密校验器并逆 30 轮 Feistel | Python 3 标准库 | 将题目附件 `elfstudy` 放到同目录，执行 `python solve.py` |
| `restore_call.py` | 把隐藏 Rela 第 12 条写回 `0x3b34`，生成 `elfstudy_restored` 用于动态验证 | Python 3 标准库 | `python restore_call.py`，再执行 `./elfstudy_restored 'flag{...}'` |
| `dump_page.c` | ptrace 在加载完成后 dump RX 页，用于静态/动态结果交叉验证 | gcc、Linux x86-64 | `gcc dump_page.c -o dump_page && ./dump_page` |
| `invert.py` | 从 dump 页反推 Feistel（`solve.py` 已合并该逻辑） | Python 3 标准库 | 可选 |
| `checker.asm`、`stub.asm` | 解密后校验器与加载期 stub 的反汇编分析稿 | 文本 | 阅读用 |

### 04 ezphp（Web）

| 文件 | 用途 | 依赖 | 运行 |
|---|---|---|---|
| `gen_payload.py` | 构造 `GuzzleHttp\Cookie\FileCookieJar` 的 PHP 序列化 payload，并转换为 NUL-safe 的 Redis Lua `EVAL` 脚本 | Python 3 标准库 | `python gen_payload.py [filename] [phpcode]` |
| `redis_ctl.py` | 通过 `/flag.php` 的 gopher SSRF 执行任意 Redis 命令 | Python 3 标准库 | 修改 `TARGET` 后执行 `python redis_ctl.py <port> <command...>` |
| `ezphp_cfg.py` | 完整利用：写入 `config/*.config.php` → Nextcloud 自动 include → 命令执行 | Python 3 标准库，需与本目录其他脚本同目录 | `python ezphp_cfg.py probe` 或 `python ezphp_cfg.py cmd '<command>'` |
| `cfg_rce.py`、`inject_shell.py` | 早期/辅助验证脚本（配置路径探测、shell 注入），内置占位 SID | Python 3 标准库 | 需先替换 `HOST`、`SID`、`SESSION_NAME` |
| `success_evidence.txt` | RCE 成功证据：`cat /flag` 与诱饵文件对比 | 文本 | 阅读用 |

### 05 frozen（Crypto）

| 文件 | 用途 | 依赖 | 运行 |
|---|---|---|---|
| `solve.py` | 解析 banner 中的 memory，重建 Falcon 树与 G00，逆 negacyclic FFT 恢复 D，派生密钥流解密 flag | Python 3、numpy | `python solve.py banner_new.txt` |
| `capture_solve.py` | 连接容器抓取 banner 并调用 `solve.py` 直接解算 | Python 3、numpy | `python capture_solve.py <host> <port>` |
| `banner_new.txt` | 新实例 banner（公钥、memory、密文），复现输入 | 文本 | 作为 `solve.py` 输入 |

## 复现环境

- Python 3.13，第三方依赖：`requests`、`numpy`
- Linux x86-64：ELFStudy 动态验证、easytl 本地调试
- gcc：ELFStudy 的 `dump_page.c`
- 所有远端地址均为比赛期间的临时实例，已失效；复现时替换为新的授权靶机

## 公开前检查

1. 本作品集仅用于授权 CTF 比赛、教学与安全研究，禁止用于未授权测试。
2. WP 中包含比赛期间的 flag 与临时靶机地址；公开发布前可按需替换或打码。
3. 平台截图未收录：截图中包含 team token，公开前必须打码。
4. 题目附件（二进制、源码包）未收录，复现时使用比赛原附件。
5. 脚本保留原始利用逻辑，未做通用化或武器化改造。

## 验证状态

| 题目 | 平台结果 |
|---|---|
| cwp | 提交通过（100 分） |
| easytl | 提交通过（100 分） |
| ELFStudy | 提交通过（100 分） |
| ezphp | 提交通过（100 分，队友提交） |
| frozen | 提交通过（100 分） |
