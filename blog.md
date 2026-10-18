# 从零到一张偶像演唱会画廊：安装 OpenCode、加载 Skill、本地跑起来

> 目标：用 [OpenCode](https://opencode.ai/v2/docs/) 调用 **pop** 这个技能（仓库名
> `concert_photo_gallery`，ID 起成了短名 `pop`，好在 TUI 里 `@pop` 唤起），
> 从一句「帮我找某某偶像某场演唱会的照片，做成画廊」开始，
> 最后在本机得到一个可以在浏览器里打开的静态相册站点。
>
> 全程不需要写后端、不需要云服务，最后你会有一个 `index.html` + 一堆照片 + 一条
> `python3 -m http.server` 命令。

本文分三段：**装工具 → 装技能 → 真正把画廊搭出来**。第三段会说明为什么不能直接照抄技能原文
（技能原文是为沙箱环境写的），并给出本地可直接运行的替代方案。

---

## ⚠️ 先读这一条：使用边界

本文教的是**个人存档**的技术流程，不是版权规避手段。动手前请接受以下边界，否则不要继续：

- **仅限个人查看。** 演唱会照片的著作权归拍摄者（粉丝站、站姐）与主办方所有。不要二次发布、
  不要商用、不要上传到公开图库或社交平台。
- **只抓公开可达的内容。** 不绕过登录、付费墙、DRM、验证码或防爬措施。文中的请求头只是部分
  CDN 的正常回源要求；**一旦站点拒绝或封禁，就当这个来源不存在，换源或直接放弃**——不要换 IP、
  不要构造绕过方案。
- **遵守站点条款与 `robots.txt`。** 下载前先看目标站的 ToS / robots 是否允许。批量抓取会给对方
  造成负担，请限制并发、不要循环重试。
- **优先官方与授权来源。** 官方 SNS、官方新闻图、已获授权的粉丝站，永远优于来源不明的聚合站。
- **权利人可要求删除。** 若你是照片权利人并希望移除相关内容，见仓库根目录的 `DISCLAIMER.md`。
- **本地法域差异。** 「个人使用」的例外范围各国不同，请自行确认你所在地的规定。

---

## ⚡ 一键安装（不想手动就只跑这一条）

下面的脚本把「§1 装 OpenCode + §2 装技能」合成一条命令，**不需要 git**：

```sh
curl -fsSL https://laotree.github.io/opencode-concert-gallery/install.sh | bash
```

它依次做四件事：

1. **检查环境** —— 系统 / 架构 / `curl` / `python3`（缺 python 会提示怎么装）；
2. **安装 OpenCode V2** —— 已经是 V2 就跳过，检测到旧版会升级；
3. **下载技能** —— 把 `SKILL.md` 和 `build_gallery.py` 放进
   `~/concert-photo-gallery/.opencode/skills/pop/`（目录名就是技能 ID，所以唤起时是 `@pop`）；
4. **校验** —— 检查 frontmatter 里的 `description`、以及 `build_gallery.py` 的语法。

重复执行安全（幂等）。常用选项：

| 选项 | 作用 |
| --- | --- |
| `--dir DIR` | 换项目目录（默认 `~/concert-photo-gallery`） |
| `--skills-dir DIR` | 换技能根目录（默认 `.opencode/skills`） |
| `--no-opencode` | 只装技能，不动 OpenCode |
| `--local PATH` | 从本地 `dist/` 拷贝，不走网络 |
| `-h, --help` | 查看全部选项 |

Windows 用 PowerShell：

```powershell
irm https://laotree.github.io/opencode-concert-gallery/install.ps1 | iex
```

装完直接用就跳到 §3；想搞清楚每一步为什么这么做，继续往下读。

> 脚本下载的 `SKILL.md` / `build_gallery.py` 来自站点上的 `dist/pop/` 目录。那个目录
> **不在仓库里**：由 CI 用 `build.py` 从**本文 §3 和 §4 的代码块**自动生成、随站点发布 ——
> 所以「文档里写的」和「脚本装下去的」永远一致，仓库里只留源码（`.opencode/` 也一样不入库）。

---

## 0. 先说清楚我们要做的事

OpenCode 是一个开源 AI 编码代理，有终端（TUI）、桌面端和网页端三种形态。它的一个核心设计是
**Skill（技能）**：一份 Markdown 写的操作手册，平时只把「标题 + 描述」暴露给模型，当任务匹配时
模型才用 `skill` 工具把正文加载进上下文。

`pop` 就是这样一个技能：它描述了「解析偶像/场次 → 搜图 → 校验下载 → 出成本地画廊」
这一整条工作流。我们要做的是：

1. 在本机装好 OpenCode V2；
2. 把当前仓库里的这个技能放进 OpenCode 能发现的位置；
3. 让它在本机（而不是沙箱）真正跑通一次，产出画廊站点。

---

## 1. 安装 OpenCode V2

### 1.1 选一种安装方式

```sh
# 官方脚本（最快，自动选平台二进制）
curl -fsSL https://opencode.ai/v2/install | bash

# 或者 Homebrew
brew install anomalyco/tap/opencode-v2

# 或者任意 Node 包管理器
npm  install -g @opencode/cli
bun  install -g --trust @opencode/cli
pnpm add -g --allow-build=@opencode/cli @opencode/cli
yarn global add @opencode/cli
```

> ⚠️ 注意版本别装错：包管理器上同时存在 V1 和 V2。
> `brew` 的 V2 公式名是 `opencode-v2`，npm 包名是 `@opencode/cli`。
> 不想用包管理器，也可以直接下独立二进制：
> - macOS：[Apple silicon](https://opencode.ai/update/api/latest/cli/opencode/opencode-darwin-arm64.zip) ·
>   [Intel](https://opencode.ai/update/api/latest/cli/opencode/opencode-darwin-x64.zip)
> - Windows：[ARM64](https://opencode.ai/update/api/latest/cli/opencode/opencode-windows-arm64.zip) ·
>   [x64](https://opencode.ai/update/api/latest/cli/opencode/opencode-windows-x64.zip)
> - Linux：[glibc x64](https://opencode.ai/update/api/latest/cli/opencode/opencode-linux-x64.tar.gz) ·
>   [musl x64](https://opencode.ai/update/api/latest/cli/opencode/opencode-linux-x64-musl.tar.gz)
>
> Windows 暂不支持包管理器安装，请用上面的独立二进制。
> 另外如果是从旧版升级，V2 的**服务端 API 和插件 API 有破坏性变更**，配置和技能本身是向后兼容的。

### 1.2 验证安装

```sh
opencode --version
# opencode v2.0.32   ← 只要主版本是 2 就对了

opencode service status
```

OpenCode 是**客户端 / 后台服务**架构：TUI 连的是本机一个共享的后台服务，会话、配置、插件、
工具执行都在服务里。服务一般会自动拉起；如果卡住了：

```sh
opencode service restart
opencode service status
```

### 1.3 接入模型

```sh
cd ~/concert-photo-gallery     # 就在这个技能仓库里开一个新会话
opencode
```

进入 TUI 后按 `/connect` 选一个 provider 登录（OpenCode 内置支持很多家模型；也可以用
[OpenCode Console](https://opencode.ai/v2/docs/console/) 一站式接入）。想换默认模型，写进
`~/.config/opencode/opencode.json`：

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "<provider>/<model-id>"
}
```

---

## 2. 把 pop 加载进来

### 2.1 OpenCode 到底从哪里找技能

OpenCode 会自动扫描下面这些位置。**技能按 ID 选取，同一个 ID 出现多次时，优先级更高的那个生效**。
优先级从低到高是：

| 顺序 | 来源 |
| --- | --- |
| 1 | 内置技能（built-in） |
| 2 | `.claude/skills`（全局 `~/.claude/skills` 优先，然后从最远祖先目录走到当前目录） |
| 3 | `.agents/skills`（同上顺序） |
| 4 | `~/.config/opencode/skills` |
| 5 | 项目 `.opencode/skills`（从项目根走到当前目录） |
| 6 | `opencode.json(c)` 里显式配置的 `skills` 数组（按配置优先级 + 数组顺序） |

每个位置里可以放两种形态：

```text
skills/
├── some-note.md              # 位于源码根目录的 .md 文件，ID = 文件名
└── pop/
    └── SKILL.md              # 任意深度的 SKILL.md，ID = 所在目录名
```

**关键点：技能 ID 由路径决定，跟 YAML/frontmatter 里的 `name` 无关，而且大小写敏感。**
所以 `.opencode/skills/pop/SKILL.md` 的 ID 就是 **`pop`**，在 TUI 里用 `@pop` 唤起。

> 这就是「昵称」的来源：**目录名 = ID = 唤起用的名字**。原技能叫 `concert_photo_gallery`，
> 太长，我们直接把它装进 `pop/` 目录，`@pop` 就够了。想同时保留长名，把目录复制一份即可
> （不同目录 = 两个独立 ID）。

### 2.2 当前仓库的技能缺了两样东西

看仓库根目录：

```text
concert_photo_gallery/
├── SKILL.md     # 正文很完整，但没有任何 frontmatter
└── skill.yaml   # name / title / description / category
```

两个问题：

1. **`SKILL.md` 没有 frontmatter。** OpenCode 需要 `description` 才会把技能广告给模型
   （否则模型根本不知道它的存在，也就不会主动加载）。
2. **`skill.yaml` 是发布方自己的元数据，OpenCode 不读它。** 真正生效的只有 `SKILL.md`
   顶部的 frontmatter。

另外注意 ID 规范：官方建议用 1–64 位的小写 kebab-case（`^[a-z0-9]+(-[a-z0-9]+)*$`）。
原目录名 `concert_photo_gallery` 含下划线，V2 目前不强制校验，能跑；但既然要短、要规范，
直接叫 `pop` 就两头都占了。

### 2.3 三步装好

```sh
# 1) 建目录（技能 ID 就来自这个目录名）
mkdir -p .opencode/skills/pop

# 2) 把正文挪进去
mv SKILL.md .opencode/skills/pop/SKILL.md

# skill.yaml 可以原地留着，OpenCode 不读它，不影响任何事
```

```sh
# 3) 给 SKILL.md 顶部补上 frontmatter（下一步会给完整版）
```

最简可以只有两行：

```markdown
---
name: pop
description: Find an idol's concert photos from the web and build a local static photo gallery site.
---

（下面接原来的正文）
```

**不想搬家？** 也可以原地保留这个仓库，用 `skills` 配置数组把目录挂进去——这是上面优先级表的第 6 档，
`skills` 数组是**累加**而不是覆盖，多个配置文件里的条目会合并：

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": [
    "~/concert-photo-gallery/.opencode/skills",   // 相对路径以「当前工作目录」为基准，不是配置文件所在目录
    "/opt/shared-skills",                        // 绝对路径原样使用
    "https://example.com/opencode/skills/"        // 也可以挂一个 HTTP 目录（catalog）
  ]
}
```

### 2.4 验证技能被发现了

- 在 TUI 里输入 `@`，应该能在补全列表里看到 `pop`；
- 或者直接在 prompt 里点它：**`@pop 帮我找 IVE 李瑞的演唱会照片并做成画廊`**。

这就是「显式加载」：`@skill-id` 会让模型立刻把该技能的正文读进上下文。除此之外，只要
`description` 写得够清晰、权限允许，模型在遇到相关任务时也会**自动**调用 `skill` 工具加载。

技能加载后，OpenCode 还会附带它的**基础目录**和最多 10 个邻近文件路径（方便放脚本、参考资料）。

### 2.5 权限（可选，但建议知道）

技能默认是否可用受 `skill` 权限约束，规则按顺序匹配、**最后一条命中的生效**：

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "permissions": [
    { "action": "skill", "resource": "*", "effect": "allow" },
    { "action": "skill", "resource": "internal-*", "effect": "deny" }
  ]
}
```

`allow` 直接加载；`ask` 加载前问你；`deny` 对模型隐藏且拒绝加载。想只对某个 agent 生效，
就放到 `agents.<id>.permissions` 下。

> 小技巧：如果某个技能你只想手动 `@` 调用、不想让模型自己乱触发，在它的 frontmatter 里写
> `metadata: { opencode/autoinvoke: false }`。它仍会被注册，只是不再出现在模型的可用列表里。

### 2.6 技能加载不进来的排查顺序

1. 文件必须是**根目录的 `*.md`** 或**任意深度的 `SKILL.md`**（大小写严格）；
2. 找 ID 要看**目录名**，不是 frontmatter 的 `name`；
3. 想让模型自己发现，就必须有 `description`；
4. 检查 `opencode/autoinvoke` 和当前 agent 的 `skill` 权限；
5. 有没有别的高优先级目录定义了同名 ID 把它覆盖掉；
6. 忘了重开会话——技能列表是在每一步模型调用时生成的。

---

## 3. 让技能在本地真正跑通

### 3.1 技能原文是为沙箱写的，直接跑会卡住

技能正文里出现了这些工具：

| 技能原文里的工具 | 它是什么 | 本机情况 |
| --- | --- | --- |
| `/opt/hatch/bin/image-search` | 专用图片搜索引擎二进制 | ❌ 本机没有（`/opt/hatch` 不存在） |
| `browser.search` | 沙箱里的浏览器搜索工具 | ❌ 本机 OpenCode 没这个工具 |
| `browser.spawn_task` | 沙箱里点开图集查看器的任务 | ❌ 同上 |
| `artifact.create_web_static` / `artifact.share` | 沙箱的静态站点构建器 + 分享 | ❌ 本机没有 |
| `sandbox://workspace/...` | 沙箱附件协议 | ❌ 本机不需要 |

**好消息**：技能里真正重要的部分是**方法论**——解析场次、多语言多日期搜图、`page_url` 溯源过滤、
`file` 校验字节、按 `yyyymmdd-event` 归档、盲猜 URL 一律不认、版权说明。这些跟运行环境无关，
完全可以保留。需要替换的只是**工具层**。

### 3.2 工具映射表（沙箱 → 本机）

| 能力 | 沙箱里 | 本机替代 |
| --- | --- | --- |
| 搜图 | `image-search` / `browser.search` | `websearch` + `webfetch`，多语言多日期各搜一遍 |
| 抓图集页里的直链 | `browser.spawn_task` 点查看器 | `webfetch` 抓静态 HTML；静态页只含前几张时，逐页抓 `?page=N` 或直接放弃换源 |
| 下载 + 校验 | `curl` + `file` | 一样，`curl -fsSL ... -o` 然后 `file` 过滤 |
| 附件回传 | `sandbox://workspace/...` | 直接把本地路径给用户 |
| 画廊站点 | `artifact.create_web_static` | **本地静态站**：一个 `build_gallery.py` + `index.html` |
| 分享链接 | `artifact.share` | `python3 -m http.server` 本机预览；要外发就自己打包 zip |

> 如果你确实跑在具备上述沙箱工具的环境里，那就按技能原文走；
> 本文面向的是**纯本地**场景。

### 3.3 本地适配版 SKILL.md（可以直接用）

把 `.opencode/skills/pop/SKILL.md` 换成下面这版。注意保留了原文的
「验证、去重、归档、别猜 URL、说明版权」这些硬规则，只把工具换成本机能用的：

````markdown
---
name: pop
description: Find a K-pop idol's concert photos from the web and build a local static photo gallery site. Use when the user names an idol, concert, or event and asks for photos, downloads, or a gallery.
---

# Concert Photo Gallery (local)

From the user's one-line ask (idol name, optionally a concert or date) to a local
static gallery site opened with `python3 -m http.server`.

## Identify the subject and event

- Parse the ask for the idol (name, group), the event (tour or concert name), and the date.
- Idol only → default to recent stage photos from the last year, and say so.
- Bare date (e.g. `20260321`) → confirm which event falls on it with `websearch` first.
- Verify the event with one search: tour name, date, venue, city. Keep these facts for captions.

## Find the photos

- Search with `websearch`, several phrasings per target: English
  (`Leeseo IVE DIVE INTO IVE fan concert day 1`), Chinese (`李瑞 2026 仁川 粉丝演唱会`),
  and date variants (`260321`, `2026-03-21`).
- Keep the image URL as the download locator and the page URL for provenance.
  Filter by page URL: keep only results whose page is about the target event.
  Prefer photos whose page or filename carries the event date.
- Use `webfetch` to read a gallery page when the user wants a whole set.
  Static HTML often embeds only the first photos; if the rest load through a viewer,
  try paged URLs (`?page=2`) once, otherwise switch to another source.
  Never guess or reconstruct a CDN URL pattern.

## Download and verify

- Download one candidate at a time with bounded timeouts and browser-like headers:

  ```sh
  curl -fsSL --connect-timeout 10 --max-time 60 -A 'Mozilla/5.0' \
    -H 'Referer: https://www.google.com/' -o '<dest>' '<media_url>'
  ```

  Only for assets the site already serves publicly. If the host rejects the
  request, treat that source as unavailable and move on — never work around it.

- Run `file` on every download; keep only real JPEG/PNG/WebP bytes.
  Drop 404s, HTML error pages, and hotlink-blocked hosts without retrying more than once.
- Deduplicate by URL before downloading.
- Save to `./photos/<idol>-<yyyymmdd>-<event>/` with sequential names
  (`photo-1.jpg`, ...). Optionally write `metadata.json`:

  ```json
  {
    "kicker": "IVE THE 4TH FAN CONCERT",
    "title": "李瑞",
    "latin": "LEESEO",
    "description": "《DIVE into IVE》仁川站第一天的舞台饭拍全记录。",
    "meta": { "演出": "《DIVE INTO IVE》Day 1", "日期": "2026.03.21",
              "场馆": "仁川 Inspire Arena", "收录": "25 张饭拍" },
    "cover": "photo-1.jpg",
    "credit": "Fan-taken photos, personal viewing only"
  }
  ```

  Only `title` is required; `kicker/latin/description/meta/cover` are optional and
  fall back to a minimal `title + count` layout, so old metadata still builds.

## Build the gallery

- Run the bundled builder:

  ```sh
  python3 scripts/build_gallery.py --photos ./photos/<folder> --open
  ```

  It scans image files, natural-sorts them, and writes a self-contained
  `index.html` (hero + photo wall + keyboard-accessible lightbox) into the folder.
  It reads `metadata.json` when present for the hero (kicker/name/lede), the
  meta row, the cover image, and the footer credit.
- Preview locally:

  ```sh
  python3 -m http.server 8000 --directory ./photos/<folder>
  # then open http://localhost:8000
  ```

- Keep only byte-verified downloads in the folder before building.
  Never ship a placeholder or a guessed URL.

## Deliver

- Local: hand the user the folder path, the `index.html` path, and the preview command.
- Want a single file to share? `zip -r <idol>-<event>.zip ./photos/<folder>` and give the path.

## Limits

- Image hosts go stale fast. A URL that 404s or 520s today is dead; move to the next source.
- Never present a guessed or reconstructed image URL as a real photo.
- The photos belong to their photographers. Package and share for personal viewing only,
  never for redistribution or commercial use. Say so in the reply and in the gallery footer.
- Only fetch publicly accessible pages and images. Do not use request headers to defeat
  access controls, and never work around a block: if a host refuses, pick another source.
````

> 注意：技能正文里写相对路径（比如 `scripts/build_gallery.py`）时，是相对于
> `SKILL.md` 所在目录解析的。所以把脚本放在
> `.opencode/skills/pop/scripts/build_gallery.py` 最省事。

### 3.4 让脚本随技能走

```text
.opencode/skills/pop/
├── SKILL.md
├── scripts/
│   └── build_gallery.py     ← 下一节的画廊生成器
└── references/
    └── (可选) 你想放的搜索话术清单、合规说明
```

这样技能自带工具，换台机器只拷这一个目录就能用。

---

## 4. 画廊生成器：`build_gallery.py`

零依赖，Python 3.9+ 直接跑。做四件事：**扫描图片 → 自然排序 → 生成自包含 `index.html` → 可选打开**。
版式参考 Muse「Space」页：整幅 hero（小标 → 中英姓名 → 一句话说明 → 细分割线 → 四栏元信息），
下面是带布局开关的「照片墙」，以及键盘/触屏可用的全屏灯箱。懒加载、明暗主题、窄屏自适应都是内置的。

```python
#!/usr/bin/env python3
"""Build a self-contained static photo gallery (index.html) for a folder of images.

Design language inspired by a Muse "Space" page: cinematic full-bleed hero
(kicker -> name lockup -> lede -> hairline -> meta row), then a photo wall
with layout controls and a full-screen viewer.

metadata.json (all optional except title):
{
  "title":       "张元英",                        # main name (cn)
  "latin":       "JANG WONYOUNG",                 # latin lockup next to name
  "kicker":      "IVE THE 4TH FAN CONCERT",       # small uppercase line above
  "description": "《DIVE into IVE》仁川站第二天的舞台饭拍全记录。",
  "meta": {"演出": "《DIVE INTO IVE》Day 2",
           "日期": "2026.03.22",
           "场馆": "仁川 Inspire Arena",
           "收录": "62 张饭拍"},                   # 4-col meta row inside hero
  "cover":       "photo-1.jpg",                   # hero image (default: first)
  "date":        "2026-03-22",                    # legacy, folded into meta
  "credit":      "..."
}
"""
import argparse
import html
import json
import os
import re
import sys
import webbrowser

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")


def natural_key(name):
    """photo-2.jpg < photo-10.jpg"""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", name)]


def collect_images(folder):
    files = [
        f for f in os.listdir(folder)
        if f.lower().endswith(IMAGE_EXTS) and os.path.isfile(os.path.join(folder, f))
    ]
    return sorted(files, key=natural_key)


def load_meta(folder):
    path = os.path.join(folder, "metadata.json")
    meta = {}
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                meta = json.load(fh) or {}
        except (OSError, ValueError) as exc:
            print("! metadata.json unreadable, ignoring: %s" % exc, file=sys.stderr)
    return meta


def caption_for(filename):
    stem = os.path.splitext(filename)[0]
    m = re.match(r"^[A-Za-z_-]*?(\d+)$", stem)
    if m:
        return "Photo %s" % int(m.group(1))
    return stem.replace("-", " ").replace("_", " ").strip().title()


HEAD = r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<title>__PAGETITLE__</title>
<style>
  :root {
    --bg: #ffffff;
    --panel: #f6f6f7;
    --ink: #0d0d10;
    --ink-2: #5b5b66;
    --ink-3: #8e8e99;
    --line: #e6e6ea;
    --accent: #2563eb;
    --tile-bg: #ececef;
    --hero-ink: #fff;
    --radius: 14px;
    --cols: 4;
    --gap: 14px;
    --ease: cubic-bezier(.2,.7,.2,1);
  }
  [data-theme="dark"] {
    --bg: #0b0b0d;
    --panel: #131316;
    --ink: #f3f3f6;
    --ink-2: #a7a7b2;
    --ink-3: #75757f;
    --line: #232329;
    --accent: #7aa2ff;
    --tile-bg: #17171b;
  }
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font: 15px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
          "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  img { -webkit-user-drag: none; user-select: none; }

  /* ---------- top bar (appears after hero) ---------- */
  .topbar {
    position: fixed; inset: 0 0 auto; z-index: 40; height: 56px;
    display: flex; align-items: center; gap: 14px;
    padding: 0 max(20px, env(safe-area-inset-left));
    background: color-mix(in srgb, var(--bg) 82%, transparent);
    backdrop-filter: saturate(180%) blur(14px);
    -webkit-backdrop-filter: saturate(180%) blur(14px);
    border-bottom: 1px solid var(--line);
    transform: translateY(-100%); opacity: 0;
    transition: transform .35s var(--ease), opacity .35s var(--ease);
  }
  .topbar.on { transform: none; opacity: 1; }
  .topbar .t-name { font-weight: 650; letter-spacing: .01em; }
  .topbar .t-sub { color: var(--ink-3); font-size: 13px; }
  .topbar .spacer { flex: 1; }
  .topbar .t-count { color: var(--ink-3); font-size: 13px; font-variant-numeric: tabular-nums; }

  /* ---------- hero ---------- */
  .hero {
    position: relative; isolation: isolate; color: var(--hero-ink);
    min-height: clamp(440px, 76vh, 780px);
    display: grid; align-items: end;
    overflow: hidden; background: #0b0b0d;
  }
  .hero-media { position: absolute; inset: 0; z-index: -2; }
  .hero-media img { width: 100%; height: 100%; object-fit: cover; object-position: center 28%; }
  .hero::after {
    content: ""; position: absolute; inset: 0; z-index: -1;
    background:
      linear-gradient(180deg, rgba(8,8,12,.58) 0%, rgba(8,8,12,.14) 24%,
                      rgba(8,8,12,.52) 58%, rgba(8,8,12,.92) 100%),
      radial-gradient(115% 88% at 0% 100%, rgba(6,6,10,.7) 0%, rgba(6,6,10,0) 58%);
  }
  .hero-inner {
    width: 100%; max-width: 1400px; margin: 0 auto;
    padding: 0 clamp(20px, 4vw, 48px) clamp(22px, 3.4vh, 40px);
  }
  .kicker {
    margin: 0 0 clamp(10px, 1.6vh, 18px);
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: .26em; color: rgba(255,255,255,.82);
  }
  .lockup {
    margin: 0; font-size: clamp(40px, 7.2vw, 86px);
    display: flex; align-items: baseline; flex-wrap: wrap; gap: .22em;
  }
  .lockup .cn {
    font-size: 1em; font-weight: 760;
    letter-spacing: .01em; line-height: 1.02;
    text-shadow: 0 2px 24px rgba(0,0,0,.35);
  }
  .lockup .latin {
    font-size: .6em; font-weight: 200;
    letter-spacing: .2em; text-transform: uppercase;
    color: rgba(255,255,255,.94); line-height: 1.02;
  }
  .lede {
    margin: clamp(14px, 2vh, 22px) 0 0; max-width: 60ch;
    font-size: clamp(14px, 1.15vw, 16px); line-height: 1.75;
    color: rgba(255,255,255,.9); text-wrap: pretty;
  }
  .hero hr {
    margin: clamp(18px, 2.6vh, 30px) 0 0; border: 0;
    border-top: 1px solid rgba(255,255,255,.26);
  }
  .meta {
    margin: clamp(14px, 2vh, 22px) 0 0; display: grid; gap: 10px 24px;
    grid-template-columns: repeat(auto-fit, minmax(120px, max-content));
  }
  .meta div { min-width: 0; }
  .meta dt {
    font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
    color: rgba(255,255,255,.62); margin-bottom: 3px;
  }
  .meta dd {
    margin: 0; font-size: clamp(13px, 1vw, 15px); font-weight: 600;
    color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  /* ---------- wall ---------- */
  main { max-width: 1400px; margin: 0 auto; padding: clamp(26px, 4vh, 44px) clamp(20px, 4vw, 48px) 0; }
  .section-head {
    display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
    margin-bottom: clamp(16px, 2.4vh, 24px);
  }
  .section-head h2 {
    margin: 0; font-size: clamp(17px, 1.6vw, 21px); font-weight: 700; letter-spacing: .02em;
  }
  .section-head .n { color: var(--ink-3); font-size: 13px; font-variant-numeric: tabular-nums; }
  .section-head .spacer { flex: 1; }
  .tools { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .seg {
    display: inline-flex; padding: 3px; gap: 2px;
    background: var(--panel); border: 1px solid var(--line); border-radius: 999px;
  }
  .seg button {
    appearance: none; border: 0; cursor: pointer; color: var(--ink-2);
    background: transparent; border-radius: 999px; padding: 6px 12px;
    font: inherit; font-size: 13px; font-weight: 600; line-height: 1;
    transition: background .18s var(--ease), color .18s var(--ease);
  }
  .seg button:hover { color: var(--ink); }
  .seg button.on { background: var(--bg); color: var(--ink); box-shadow: 0 1px 3px rgba(0,0,0,.12); }
  .icon {
    appearance: none; cursor: pointer; color: var(--ink-2);
    background: var(--panel); border: 1px solid var(--line);
    width: 34px; height: 34px; border-radius: 999px; font-size: 15px; line-height: 1;
  }
  .icon:hover { color: var(--ink); }

  .wall { --gap: 14px; }
  .wall[data-layout="masonry"] { column-gap: var(--gap); column-count: var(--cols); }
  .wall[data-layout="masonry"] .tile { break-inside: avoid; margin: 0 0 var(--gap); }
  .wall[data-layout="grid"] {
    display: grid; gap: var(--gap);
    grid-template-columns: repeat(var(--cols), minmax(0, 1fr));
  }
  .tile {
    position: relative; margin: 0; border-radius: var(--radius);
    overflow: hidden; background: var(--tile-bg);
  }
  .wall[data-layout="grid"] .tile img { aspect-ratio: 4 / 5; }
  .tile img {
    display: block; width: 100%; height: auto;
    cursor: zoom-in; transition: transform .5s var(--ease), filter .3s var(--ease);
  }
  .wall[data-layout="grid"] .tile img { height: 100%; object-fit: cover; }
  .tile:hover img { transform: scale(1.035); }
  .tile .badge {
    position: absolute; top: 10px; right: 10px; padding: 3px 9px;
    font-size: 11px; font-weight: 700; font-variant-numeric: tabular-nums;
    color: #fff; background: rgba(8,8,12,.5); border-radius: 999px;
    backdrop-filter: blur(6px); opacity: 0; transition: opacity .2s var(--ease);
  }
  .tile:hover .badge, .tile:focus-within .badge { opacity: 1; }
  .tile figcaption { display: none; }

  footer {
    max-width: 1400px; margin: 0 auto;
    padding: clamp(28px, 5vh, 52px) clamp(20px, 4vw, 48px)
             calc(48px + env(safe-area-inset-bottom));
    color: var(--ink-3); font-size: 12.5px; line-height: 1.8;
  }
  footer .credit { margin: 0 0 6px; max-width: 92ch; }
  footer .colophon { margin: 0; color: var(--ink-3); opacity: .8; }

  /* ---------- lightbox ---------- */
  .lb { position: fixed; inset: 0; z-index: 90; display: none; background: rgba(6,6,9,.96); }
  .lb.on { display: grid; grid-template-rows: auto 1fr auto; }
  .lb-top {
    display: flex; align-items: center; gap: 12px;
    padding: max(12px, env(safe-area-inset-top)) 16px 12px;
    color: #dcdce4;
  }
  .lb-count { font-size: 13px; font-variant-numeric: tabular-nums; letter-spacing: .04em; }
  .lb-top .spacer { flex: 1; }
  .lb-btn {
    appearance: none; border: 1px solid rgba(255,255,255,.18); cursor: pointer;
    background: rgba(255,255,255,.07); color: #fff; text-decoration: none;
    border-radius: 999px; padding: 7px 14px; font: inherit; font-size: 13px; font-weight: 600;
    transition: background .18s var(--ease);
  }
  .lb-btn:hover { background: rgba(255,255,255,.16); }
  .lb-stage { position: relative; display: grid; place-items: center; min-height: 0; padding: 0 8px; }
  .lb-img {
    max-width: min(94vw, 1600px); max-height: 100%; border-radius: 10px;
    box-shadow: 0 24px 80px rgba(0,0,0,.55);
  }
  .lb-nav {
    position: absolute; top: 50%; transform: translateY(-50%);
    width: 46px; height: 46px; border-radius: 999px; cursor: pointer;
    background: rgba(255,255,255,.1); color: #fff; border: 0;
    font-size: 22px; line-height: 1; display: grid; place-items: center;
    transition: background .18s var(--ease);
  }
  .lb-nav:hover { background: rgba(255,255,255,.22); }
  #lbPrev { left: max(12px, env(safe-area-inset-left)); }
  #lbNext { right: max(12px, env(safe-area-inset-right)); }
  .lb-strip {
    display: flex; gap: 8px; overflow-x: auto; padding: 12px 16px max(16px, env(safe-area-inset-bottom));
    scrollbar-width: none;
  }
  .lb-strip::-webkit-scrollbar { display: none; }
  .lb-strip img {
    width: 62px; height: 62px; object-fit: cover; border-radius: 8px;
    cursor: pointer; opacity: .5; flex: 0 0 auto;
    transition: opacity .2s var(--ease), outline-color .2s var(--ease);
    outline: 2px solid transparent;
  }
  .lb-strip img:hover { opacity: .85; }
  .lb-strip img.on { opacity: 1; outline-color: var(--accent); }

  :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }

  @media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
  }
  @media (max-width: 720px) {
    .hero { min-height: clamp(500px, 84svh, 780px); }
    .lockup { display: block; font-size: clamp(38px, 11vw, 54px); }
    .lockup .latin { display: block; margin-top: .16em; letter-spacing: .16em; }
    .lede { max-width: none; }
    .meta { grid-template-columns: 1fr 1fr; }
    .section-head .spacer { display: none; }
    .tools { width: 100%; }
    .lb-strip img { width: 50px; height: 50px; }
  }
</style>
</head>
<body>

<div class="topbar" id="topbar">
  <span class="t-name">__TITLE__</span>
  <span class="t-sub">__LATIN__</span>
  <span class="spacer"></span>
  <span class="t-count">__COUNT__ 张</span>
</div>

<header class="hero" id="hero">
  <div class="hero-media"><img src="__COVER__" alt="__PAGETITLE__" fetchpriority="high"></div>
  <div class="hero-inner">
    __KICKER__
    <h1 class="lockup">
      <span class="cn">__TITLE__</span>
      __LATIN_SPAN__
    </h1>
    __LEDE__
    __HR__
    __META__
  </div>
</header>

<main>
  <div class="section-head">
    <h2>照片墙</h2>
    <span class="n">__COUNT__ 张</span>
    <span class="spacer"></span>
    <div class="tools">
      <div class="seg" role="group" aria-label="布局">
        <button type="button" data-layout="masonry" class="on">瀑布</button>
        <button type="button" data-layout="grid">网格</button>
      </div>
      <div class="seg" role="group" aria-label="每行张数">
        <button type="button" data-cols="2">2</button>
        <button type="button" data-cols="3">3</button>
        <button type="button" data-cols="4" class="on">4</button>
        <button type="button" data-cols="5">5</button>
      </div>
      <button type="button" class="icon" id="themeBtn" aria-label="切换明暗主题" title="切换明暗主题">&#9681;</button>
    </div>
  </div>
  <div class="wall" id="wall" data-layout="masonry" data-cols="4">
__ITEMS__
  </div>
</main>

<footer>
  <p class="credit">__CREDIT__</p>
  <p class="colophon">本地生成 · OpenCode · pop</p>
</footer>

<div class="lb" id="lb" role="dialog" aria-modal="true" aria-label="照片查看器">
  <div class="lb-top">
    <span class="lb-count" id="lbCount">1 / 1</span>
    <span class="spacer"></span>
    <a class="lb-btn" id="lbDl" download>下载</a>
    <button type="button" class="lb-btn" id="lbClose" aria-label="关闭">关闭</button>
  </div>
  <div class="lb-stage" id="lbStage">
    <button type="button" class="lb-nav" id="lbPrev" aria-label="上一张">&#8249;</button>
    <img class="lb-img" id="lbImg" alt="">
    <button type="button" class="lb-nav" id="lbNext" aria-label="下一张">&#8250;</button>
  </div>
  <div class="lb-strip" id="lbStrip"></div>
</div>

<script>
(function () {
  var TILES = Array.prototype.slice.call(document.querySelectorAll('#wall .tile'));
  var DATA = TILES.map(function (t) {
    var img = t.querySelector('img');
    return { src: img.getAttribute('src'), cap: (t.querySelector('figcaption') || {}).textContent || '' };
  });
  var N = DATA.length;
  if (!N) return;

  /* ---------- layout controls ---------- */
  var wall = document.getElementById('wall');
  var cols = 4, mode = 'masonry';
  function applyCols() {
    var w = window.innerWidth;
    var cap = w < 560 ? 2 : w < 900 ? 3 : 5;
    wall.style.setProperty('--cols', Math.min(cols, cap));
  }
  function segHandler(sel, attr, onPick) {
    var btns = Array.prototype.slice.call(document.querySelectorAll(sel + ' button'));
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        btns.forEach(function (x) { x.classList.remove('on'); });
        b.classList.add('on');
        onPick(b.getAttribute(attr));
      });
    });
  }
  segHandler('.seg[aria-label="布局"]', 'data-layout', function (v) {
    mode = v; wall.setAttribute('data-layout', v);
  });
  segHandler('.seg[aria-label="每行张数"]', 'data-cols', function (v) {
    cols = parseInt(v, 10); applyCols();
  });
  applyCols();
  window.addEventListener('resize', applyCols);

  /* ---------- theme ---------- */
  var root = document.documentElement;
  try {
    var saved = localStorage.getItem('gallery-theme');
    if (saved) root.setAttribute('data-theme', saved);
    else if (window.matchMedia('(prefers-color-scheme: dark)').matches) root.setAttribute('data-theme', 'dark');
  } catch (e) {}
  document.getElementById('themeBtn').addEventListener('click', function () {
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('gallery-theme', next); } catch (e) {}
  });

  /* ---------- top bar ---------- */
  var topbar = document.getElementById('topbar');
  var hero = document.getElementById('hero');
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (es) {
      topbar.classList.toggle('on', es[0].intersectionRatio < 0.06);
    }, { threshold: [0, 0.06, 1] }).observe(hero);
  }

  /* ---------- lightbox ---------- */
  var lb = document.getElementById('lb');
  var lbImg = document.getElementById('lbImg');
  var lbCount = document.getElementById('lbCount');
  var lbStrip = document.getElementById('lbStrip');
  var lbDl = document.getElementById('lbDl');
  var lbStage = document.getElementById('lbStage');
  var idx = 0, stripBuilt = false;

  function buildStrip() {
    if (stripBuilt) return;
    var frag = document.createDocumentFragment();
    DATA.forEach(function (d, i) {
      var im = document.createElement('img');
      im.src = d.src; im.alt = ''; im.loading = 'lazy';
      im.addEventListener('click', function () { show(i); });
      frag.appendChild(im);
    });
    lbStrip.appendChild(frag);
    stripBuilt = true;
  }
  function markStrip() {
    Array.prototype.forEach.call(lbStrip.children, function (c, i) {
      c.classList.toggle('on', i === idx);
    });
    var act = lbStrip.children[idx];
    if (act && act.scrollIntoView) act.scrollIntoView({ block: 'nearest', inline: 'center' });
  }
  function preload(i) {
    var j = (i + N) % N;
    if (!DATA[j]._p) { DATA[j]._p = new Image(); DATA[j]._p.src = DATA[j].src; }
  }
  function show(i) {
    idx = ((i % N) + N) % N;
    var d = DATA[idx];
    lbImg.src = d.src;
    lbImg.alt = d.cap;
    lbCount.textContent = (idx + 1) + ' / ' + N;
    try { lbDl.href = d.src; lbDl.setAttribute('download', d.src.split('/').pop()); } catch (e) {}
    buildStrip(); markStrip();
    preload(idx + 1); preload(idx - 1);
  }
  function open(i) {
    show(i);
    lb.classList.add('on');
    document.body.style.overflow = 'hidden';
  }
  function close() {
    lb.classList.remove('on');
    document.body.style.overflow = '';
    lbImg.removeAttribute('src');
  }

  TILES.forEach(function (t, i) {
    var img = t.querySelector('img');
    img.addEventListener('click', function () { open(i); });
    img.setAttribute('tabindex', '0');
    img.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(i); }
    });
  });
  document.getElementById('lbClose').addEventListener('click', close);
  document.getElementById('lbPrev').addEventListener('click', function () { show(idx - 1); });
  document.getElementById('lbNext').addEventListener('click', function () { show(idx + 1); });
  lbStage.addEventListener('click', function (e) { if (e.target === lbStage) close(); });
  document.addEventListener('keydown', function (e) {
    if (!lb.classList.contains('on')) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(idx - 1);
    else if (e.key === 'ArrowRight') show(idx + 1);
    else if (e.key === 'Home') show(0);
    else if (e.key === 'End') show(N - 1);
  });

  /* touch swipe */
  var sx = 0, sy = 0;
  lbStage.addEventListener('touchstart', function (e) {
    sx = e.changedTouches[0].clientX; sy = e.changedTouches[0].clientY;
  }, { passive: true });
  lbStage.addEventListener('touchend', function (e) {
    var dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
    if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy)) show(idx + (dx < 0 ? 1 : -1));
  }, { passive: true });
})();
</script>
</body>
</html>
"""


def build(folder, title=None, credit=None, open_browser=False):
    folder = os.path.abspath(os.path.expanduser(folder))
    if not os.path.isdir(folder):
        sys.exit("no such folder: %s" % folder)

    images = collect_images(folder)
    if not images:
        sys.exit("no images found in %s" % folder)

    meta = load_meta(folder)
    title = title or meta.get("title") or os.path.basename(folder)
    credit = credit or meta.get("credit") or "Fan-taken photos — personal viewing only."
    latin = (meta.get("latin") or "").strip()
    kicker = (meta.get("kicker") or "").strip()
    lede = (meta.get("description") or "").strip()

    cover = meta.get("cover")
    if not cover or cover not in images:
        cover = images[0]
    cover_src = "./" + cover.replace(" ", "%20")

    # meta row: explicit dict wins, else fold legacy date + count in.
    cells = meta.get("meta")
    if not isinstance(cells, dict) or not cells:
        cells = {}
        if meta.get("date"):
            cells["日期"] = meta["date"]
        cells["收录"] = "%d 张" % len(images)
    meta_html = "".join(
        "\n      <div><dt>%s</dt><dd>%s</dd></div>" % (html.escape(str(k)), html.escape(str(v)))
        for k, v in cells.items()
    )

    items = []
    for i, name in enumerate(images, 1):
        src = "./" + name.replace(" ", "%20")
        cap = html.escape(caption_for(name))
        items.append(
            '<figure class="tile"><img src="%s" alt="%s" loading="lazy" decoding="async">'
            '<span class="badge">%d</span><figcaption>%s</figcaption></figure>'
            % (src, cap, i, cap)
        )

    doc = HEAD
    repl = {
        "__PAGETITLE__": html.escape(
            "%s %s" % (title, "— %s" % kicker if kicker and kicker not in title else "")
        ).replace("  ", " ").strip(),
        "__TITLE__": html.escape(str(title)),
        "__LATIN__": html.escape(latin),
        "__LATIN_SPAN__": '<span class="latin">%s</span>' % html.escape(latin) if latin else "",
        "__KICKER__": '<p class="kicker">%s</p>' % html.escape(kicker) if kicker else "",
        "__LEDE__": '<p class="lede">%s</p>' % html.escape(lede) if lede else "",
        "__HR__": "<hr>" if (lede or meta_html) else "",
        "__META__": ('<dl class="meta">%s\n    </dl>' % meta_html) if meta_html else "",
        "__COUNT__": str(len(images)),
        "__COVER__": cover_src,
        "__CREDIT__": html.escape(credit),
        "__ITEMS__": "\n".join("  " + x for x in items),
    }
    for k, v in repl.items():
        doc = doc.replace(k, v)

    out = os.path.join(folder, "index.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print("wrote %s (%d photos)" % (out, len(images)))
    if open_browser:
        webbrowser.open("file://" + out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--photos", required=True, help="folder containing the images")
    ap.add_argument("--title", help="gallery title (default: metadata.json / folder name)")
    ap.add_argument("--credit", help="footer credit line")
    ap.add_argument("--open", action="store_true", help="open the gallery in the browser")
    args = ap.parse_args()
    build(args.photos, args.title, args.credit, args.open)


if __name__ == "__main__":
    main()
```

用法：

```sh
python3 .opencode/skills/pop/scripts/build_gallery.py \
  --photos ./photos/leeseo-20260321-incheon-fancon \
  --title "IVE Leeseo — DIVE INTO IVE in Incheon (2026-03-21)" \
  --open
```

生成的 `index.html` 引用的都是同目录下的相对路径图片，所以**整个文件夹拷到哪里都能看**，也能直接
丢进任何静态托管。想看「像网站一样」的效果（而不是 `file://`）就起个本地服务：

```sh
python3 -m http.server 8000 --directory ./photos/leeseo-20260321-incheon-fancon
# 浏览器打开 http://localhost:8000
```

---

## 5. 一次完整的实战对话

技能装好后，你在 TUI 里其实只需要说一句话。下面是一次典型的完整流程（左右是「你做什么 / 会发生什么」）：

**① 发起**

```text
@pop 帮我找 IVE 李瑞 DIVE INTO IVE 仁川粉丝演唱会第一天的照片，
全部下载下来做成本地画廊
```

技能被加载后，模型会：

- 解析出 **偶像=李瑞(IVE)**、**场次=DIVE INTO IVE 仁川粉丝演唱会**、**日期=第一天**；
- 先用一次搜索核实场次：巡演名、日期、场馆、城市，留作标题和文件名。

**② 搜图**（多语言 × 多日期，这是技能里最值钱的一条经验）

```text
英文:  Leeseo IVE DIVE INTO IVE fan concert day 1 Incheon
中文:  李瑞 2026 仁川 粉丝演唱会 第一天
日期:  260321 / 2026-03-21
```

每个结果记两样东西：**图片直链**（下载用）和**页面地址**（溯源用）。然后**按页面地址过滤**——
只保留页面确实在讲这场演唱会的，优先文件名/页面里带日期的。

**③ 下载并校验**（这一步决定了画廊里有没有坏图）

```sh
curl -fsSL --connect-timeout 10 --max-time 60 -A 'Mozilla/5.0' \
  -H 'Referer: https://www.google.com/' \
  -o ./photos/leeseo-20260321-incheon-fancon/photo-1.jpg '<media_url>'
file ./photos/leeseo-20260321-incheon-fancon/photo-1.jpg
```

这段命令**只对站点本来就公开提供的资源使用**。如果对方站点的 ToS 或 `robots.txt` 不允许抓取，
或者它明确拒绝了这个请求，就直接跳过这个来源——不要改 IP、不要构造绕过方案。

`file` 必须报出真实的 JPEG/PNG/WebP。报成 `HTML document` 就是被拦或 404 了——**删掉、换源，
不要重试第二次**。下载前先按 URL 去重。

**④ 归档**

```text
photos/
└── leeseo-20260321-incheon-fancon/
    ├── photo-1.jpg
    ├── photo-2.jpg
    ├── ...
    └── metadata.json      # hero 文案 / 元信息 / 署名（可选）
```

**⑤ 出画廊并预览**

```sh
python3 .opencode/skills/pop/scripts/build_gallery.py \
  --photos ./photos/leeseo-20260321-incheon-fancon --open

python3 -m http.server 8000 --directory ./photos/leeseo-20260321-incheon-fancon
```

**⑥ 收尾**：让模型在回复里写清照片是**粉丝拍摄、仅供个人查看**——这句话也会出现在画廊页脚。

---

## 6. 验收清单

跑完一次，对照这份清单，都打勾才算真的搭好了：

- [ ] `opencode --version` 显示 `v2.x`
- [ ] TUI 里输入 `@` 能看到 `pop`
- [ ] 技能正文里描述的流程真的在执行（而不是模型自由发挥）
- [ ] 每张进画廊的图都过了 `file` 校验，没有 HTML 错误页混进来
- [ ] 文件夹命名是 `<idol>-<yyyymmdd>-<event>/`，照片是 `photo-N.jpg` 顺序
- [ ] `index.html` 已生成，网格 + 灯箱可用，键盘 `←` `→` `Esc` 有效
- [ ] 页脚有版权说明
- [ ] 整个 `photos/<folder>` 拷到别处仍能正常打开

---

## 7. 合规与注意事项

完整的红线写在文首的「使用边界」和根目录 `DISCLAIMER.md` 里，这里是清单化版本：

- **图片版权属于拍摄者。** 这套流程只适合**个人观看**——不要二次分发、不要用于商业用途。
  把这句话写进回复和画廊页脚，也是技能里明确要求的。
- **不要公开托管抓来的照片。** 生成的 `index.html` 只在本机或局域网预览。
  把它挂到公开域名、公开对象存储、公开图床，就等于二次分发。
- **只抓公开可达的内容。** 不绕登录、付费墙、DRM、验证码、防爬；请求头不是绕过手段。
  站点明确拒绝时，**换源或放弃**，不要构造绕过方案（换 IP、模拟验证码等一律不做）。
- **遵守 ToS 与 `robots.txt`。** 下载前先确认目标站允许；控制并发、不要无限重试，
  避免给对方造成负担。
- **优先官方与授权来源。** 官方 SNS / 新闻图 / 已授权粉丝站 > 来源不明的聚合站。
- **可由权利人要求删除。** 仓库根目录 `DISCLAIMER.md` 里留了处理方式。
- **注意所在法域。** 「个人使用」的例外范围因国家/地区而异，自行确认。
- **不要盲猜图片 URL。** 技能原文特别强调：「绝不要把一个猜测或重建出来的 URL 当成真实照片」。
  只有字节校验过的下载，或构建器真正渲染出来的图，才能算数。
- **图片站点失效极快。** 今天 404/520 的地址就是死了，**换源**，别硬刚。
- 如果某个图集页静态 HTML 只含前几张、其余要查看器动态加载：本机没有浏览器自动化时，
  试一次分页 URL 就行，不行就换源。**别为了凑数量造假数据**。

---

## 8. 排错速查

| 现象 | 原因 / 处理 |
| --- | --- |
| 模型不知道有这个技能 | `SKILL.md` 缺 `description`，或没放在扫描目录里 |
| `@xxx` 补全里找不到 | ID 用的是**目录名**；目录名大小写、下划线都要对 |
| 加载的是旧内容 | 有更高优先级的同名 ID 把它覆盖了（见 §2.1 优先级顺序） |
| 技能加载被拒 | `skill` 权限是 `deny`/`ask`，或 agent 级覆盖了全局规则 |
| 技能里让用的工具不存在 | 那是沙箱工具（`image-search`、`artifact.*`）——按 §3.2 换成 `websearch`/`webfetch`/本地脚本 |
| 画廊全是坏图 | 少了 `file` 校验；加回 §5-③ 那一步 |
| 页面打开是「白板」 | 直接双击 `index.html` 也行，但建议用 `python3 -m http.server` |
| TUI 行为怪异、会话丢失 | `opencode service restart`，再 `opencode service status`；日志在 `~/.local/share/opencode/log/opencode.log` |

---

## 9. 一页纸速通版

```sh
# 1) 装
curl -fsSL https://opencode.ai/v2/install | bash
opencode --version            # 要 v2.x

# 2) 装技能
mkdir -p .opencode/skills/pop/scripts
mv SKILL.md .opencode/skills/pop/SKILL.md
# 给 SKILL.md 顶部加 frontmatter（name + description），正文按 §3.3 换成本地工具
# 把 §4 的 build_gallery.py 存到 scripts/

# 3) 用
cd ~/concert-photo-gallery && opencode
# 在 TUI 里：@pop 帮我找 <偶像> <场次> 的照片并做成本地画廊

# 4) 看
python3 -m http.server 8000 --directory ./photos/<folder>
# → http://localhost:8000
```

就这些。装好一次之后，以后每场演唱会只要一句话、一个新文件夹。

---

## 10. 许可

本站的**文字与代码**（含 `build_gallery.py`）以 [MIT](./LICENSE) 许可发布：
可自由使用、修改、再分发，保留版权声明即可。

**照片不在其中。** `photos/` 下的图片版权归各拍摄者所有，MIT 不适用，仅供个人
查看 —— 详见 [DISCLAIMER.md](./DISCLAIMER.md)。
