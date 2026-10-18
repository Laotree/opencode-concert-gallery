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
| `--local PATH` | 从本地拷贝（如 `--local skill/pop`），不走网络 |
| `-h, --help` | 查看全部选项 |

Windows 用 PowerShell：

```powershell
irm https://laotree.github.io/opencode-concert-gallery/install.ps1 | iex
```

装完直接用就跳到 §3；想搞清楚每一步为什么这么做，继续往下读。

> 技能本体就在仓库里（[`skill/pop/`](https://github.com/Laotree/opencode-concert-gallery/tree/main/skill/pop)），
> 随源码一起发布到站点 —— 文档里看到的、链接点开的、脚本装下去的，始终是同一份文件。

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
```

其余方式：Homebrew `brew install anomalyco/tap/opencode-v2`；Node 包管理器
`npm install -g @opencode/cli`（bun / pnpm / yarn 换成对应的包管理器命令即可）。

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
[OpenCode Console](https://opencode.ai/v2/docs/console/) 一站式接入）。想固定默认模型，
就在 `~/.config/opencode/opencode.json` 里加一行 `"model"` —— 写法见 §2.7。

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

### 2.3 装好它

技能本体就在本仓库的 `skill/pop/`（`SKILL.md` + `scripts/build_gallery.py`），装进项目里只要两条命令：

```sh
mkdir -p .opencode/skills/pop
cp -r skill/pop/. .opencode/skills/pop/
```

或者直接跑文首那条一键安装命令，它做的正是这件事。`skill.yaml` 可以原地留着，OpenCode 不读它。

**不想搬家？** 也可以原地保留这个仓库，用 `skills` 配置数组把目录挂进去——这是上面优先级表的第 6 档
（写法见 §2.7）。

### 2.4 验证技能被发现了

- 在 TUI 里输入 `@`，应该能在补全列表里看到 `pop`；
- 或者直接在 prompt 里点它：**`@pop 帮我找 IVE 李瑞的演唱会照片并做成画廊`**。

这就是「显式加载」：`@skill-id` 会让模型立刻把该技能的正文读进上下文。除此之外，只要
`description` 写得够清晰、权限允许，模型在遇到相关任务时也会**自动**调用 `skill` 工具加载。

技能加载后，OpenCode 还会附带它的**基础目录**和最多 10 个邻近文件路径（方便放脚本、参考资料）。

### 2.5 权限（可选，但建议知道）

技能默认是否可用受 `skill` 权限约束，规则按顺序匹配、**最后一条命中的生效**：
`allow` 直接加载；`ask` 加载前问你；`deny` 对模型隐藏且拒绝加载。想只对某个 agent 生效，
就放到 `agents.<id>.permissions` 下；写法见 §2.7。

> 小技巧：如果某个技能你只想手动 `@` 调用、不想让模型自己乱触发，在它的 frontmatter 里写
> `metadata: { opencode/autoinvoke: false }`。它仍会被注册，只是不再出现在模型的可用列表里。

### 2.6 技能加载不进来的排查顺序

1. 文件必须是**根目录的 `*.md`** 或**任意深度的 `SKILL.md`**（大小写严格）；
2. 找 ID 要看**目录名**，不是 frontmatter 的 `name`；
3. 想让模型自己发现，就必须有 `description`；
4. 检查 `opencode/autoinvoke` 和当前 agent 的 `skill` 权限；
5. 有没有别的高优先级目录定义了同名 ID 把它覆盖掉；
6. 忘了重开会话——技能列表是在每一步模型调用时生成的。

### 2.7 用得到的配置项

上面三处配置都写在 `opencode.json(c)` 里，可以合并成一个文件：

```jsonc
// ~/.config/opencode/opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "<provider>/<model-id>",                         // 固定默认模型（§1.3）
  "skills": [ "~/concert-photo-gallery/.opencode/skills" ], // 追加的技能根目录（§2.3），累加不覆盖
  "permissions": [                                          // 按顺序匹配，最后一条生效（§2.5）
    { "action": "skill", "resource": "*", "effect": "allow" }
  ]
}
```

放在项目根目录的 `.opencode/opencode.json` 只影响当前项目。

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

### 3.3 本地适配版 SKILL.md

完整文件在仓库里：[`skill/pop/SKILL.md`](https://github.com/Laotree/opencode-concert-gallery/blob/main/skill/pop/SKILL.md)。
它保留了原文的硬规则——**字节校验、按 URL 去重、绝不猜 URL、说明版权、拒绝绕过封锁**——
只把工具层换成上面那张映射表。真正需要看懂的只有最上面四行：

```markdown
---
name: pop
description: Find a K-pop idol's concert photos from the web and build a local static photo gallery site. Use when the user names an idol, concert, or event and asks for photos, downloads, or a gallery.
---
```

`description` 是模型判断「这个任务要不要加载我」的**唯一**依据，所以要把**触发场景**写进去
（找照片 / 下载 / 做画廊），而不是写「这是一个照片技能」这种没有信息量的句子。
正文其余部分是五节操作手册：

| 小节 | 管什么 |
| --- | --- |
| `Identify the subject and event` | 从一句话里解析偶像 / 场次 / 日期，先搜一次核对事实 |
| `Find the photos` | 中英 + 日期多种问法各搜一遍；按页面 URL 过滤出真属于这场演出的图 |
| `Download and verify` | 一次一张、`file` 验字节、按 URL 去重、存 `./photos/<idol>-<yyyymmdd>-<event>/` |
| `Build the gallery` | 调用随技能带的 `scripts/build_gallery.py`，再用 `http.server` 预览 |
| `Deliver` · `Limits` | 交付与打包；边界（别猜 URL、别绕过封锁、仅供个人查看） |

把 `.opencode/skills/pop/SKILL.md` 换成它即可（一键脚本装的就是这份）：

```sh
curl -fsSL https://laotree.github.io/opencode-concert-gallery/skill/pop/SKILL.md \
  -o .opencode/skills/pop/SKILL.md
```

> 技能正文里写相对路径（比如 `scripts/build_gallery.py`）时，是相对于 `SKILL.md` 所在目录解析的。
> 所以把脚本放在 `.opencode/skills/pop/scripts/build_gallery.py` 最省事。

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

完整脚本约 620 行、零依赖，就在技能自带的 `scripts/` 里：
[`skill/pop/scripts/build_gallery.py`](https://github.com/Laotree/opencode-concert-gallery/blob/main/skill/pop/scripts/build_gallery.py)
（[直接下载](https://laotree.github.io/opencode-concert-gallery/skill/pop/scripts/build_gallery.py)）。
用法：

```sh
python3 .opencode/skills/pop/scripts/build_gallery.py \
  --photos ./photos/leeseo-20260321-incheon-fancon \
  --title "IVE Leeseo — DIVE INTO IVE in Incheon (2026-03-21)" \
  --open
```

可选：在照片目录放一个 `metadata.json` 来定制 hero 与来源说明，只有 `title` 是必需的，
缺字段会优雅退化成最简版式：

```json
{
  "kicker": "IVE THE 4TH FAN CONCERT",
  "title": "李瑞",
  "latin": "LEESEO",
  "description": "《DIVE into IVE》仁川站第一天的舞台饭拍全记录。",
  "credit": "Fan-taken photos, personal viewing only"
}
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

红线在文首的「使用边界」和根目录 `DISCLAIMER.md` 里——**图片版权属于拍摄者，只供个人查看，
不二次分发、不商用；只抓公开可达的内容，被拒绝就换源或放弃，不构造绕过方案**。
这里只补三条最容易踩的操作细节：

- **不要公开托管抓来的照片。** 生成的 `index.html` 只在本机或局域网预览；挂到公开域名、
  公开对象存储、公开图床，就等于二次分发。
- **不要盲猜图片 URL。** 只有经过 `file` 字节校验的下载、或构建器真正渲染出来的图才算数。
- **图集页只给前几张时别硬凑。** 分页 URL 试一次，不行就换源——**不要为了凑数量造假数据**。

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
curl -fsSL https://laotree.github.io/opencode-concert-gallery/install.sh | bash   # 装 OpenCode + 技能
cd ~/concert-photo-gallery && opencode                                            # 开 TUI（/connect 登录）
# 在 TUI 里说：@pop 帮我找 <偶像> <场次> 的照片并做成本地画廊
python3 -m http.server 8000 --directory ./photos/<folder>                         # 看 → http://localhost:8000
```

就这些。装好一次之后，以后每场演唱会只要一句话、一个新文件夹。

---

## 10. 许可

本站的**文字与代码**（含 `build_gallery.py`）以 [MIT](./LICENSE) 许可发布：
可自由使用、修改、再分发，保留版权声明即可。

**照片不在其中。** `photos/` 下的图片版权归各拍摄者所有，MIT 不适用，仅供个人
查看 —— 详见 [DISCLAIMER.md](./DISCLAIMER.md)。
