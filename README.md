# Concert Photo Gallery · 教程站

一篇讲**如何用 [OpenCode](https://opencode.ai/v2/docs/) 的 Skill 在本机搭建演唱会照片画廊**的中文教程，
内容同时也是这个 GitHub Pages 站点的源文件。

## 一键安装（无需 git）

```sh
curl -fsSL https://laotree.github.io/opencode-concert-gallery/install.sh | bash
```

依次执行 **检查环境 → 安装 OpenCode V2 → 下载技能 → 校验**，产物落在
`~/concert-photo-gallery/.opencode/skills/pop/`（**目录名就是技能 ID**，所以唤起时是 `@pop`）。
幂等，可重复运行。

Windows（PowerShell）：

```powershell
irm https://laotree.github.io/opencode-concert-gallery/install.ps1 | iex
```

| 选项 | 说明 |
| --- | --- |
| `--dir DIR` | 项目目录（默认 `~/concert-photo-gallery`） |
| `--skills-dir DIR` | 技能根目录（默认 `.opencode/skills`） |
| `--id NAME` | 技能目录名 / ID（默认 `pop`，即 `@pop`） |
| `--no-opencode` | 只装技能，不动 OpenCode |
| `--local PATH` | 从本地 `dist/` 拷贝，不走网络 |
| `-h, --help` | 帮助 |

> `dist/pop/` **不入库**：由 CI（`.github/workflows/pages.yml`）用 `build.py` 从 `blog.md`
> 的代码块抽取、随站点一起发布，`install.sh` 再从站点下载它。`.opencode/` 同样不进版本库。
> 目录名即技能 ID，装好就是 `@pop`。

## 内容

| 文件 | 说明 |
| --- | --- |
| `blog.md` | 教程正文（唯一内容源） |
| `build.py` | 把 `blog.md` 渲染成 `index.html`，并抽取 `dist/pop/` |
| `.github/workflows/pages.yml` | CI：构建并发布站点（构建产物不入库） |
| `install.sh` / `install.ps1` | 一键安装脚本（macOS/Linux/WSL · Windows） |
| `SKILL.md` | `concert_photo_gallery` 技能本体 |
| `skill.yaml` | 技能元数据（OpenCode 不读取，由原发布方使用） |
| `DISCLAIMER.md` | 使用边界与版权说明 |
| `LICENSE` | MIT 许可（覆盖文字与代码，不含照片） |
| `index.html` | 站点首页 —— **构建产物，不入库** |
| `dist/pop/` | 可安装的技能文件 —— **构建产物，不入库**，`install.sh` 的下载源 |

## 构建与发布

`main` 分支只有**源码**。构建产物 `index.html` 和 `dist/pop/` 都在 `.gitignore` 里，
由 GitHub Actions 在每次 push 时生成并发布到 Pages：

```
blog.md ──► build.py ──► index.html      ┐
                     └─► dist/pop/       ┴─► Actions ──► GitHub Pages
```

本地想做同样的构建：

```sh
python3 -m pip install markdown
python3 build.py
```

改完 `blog.md` 后重新生成、本地预览：

```sh
python3 -m http.server 8000
# → http://localhost:8000
```

## 教程覆盖的内容

1. 安装 OpenCode V2（curl / brew / npm / bun / pnpm，或独立二进制）
2. 把技能放进 OpenCode 能发现的位置（技能 ID 规则、优先级、`skills` 配置数组、权限）
3. 把技能从沙箱工具适配到本机工具（`websearch` / `webfetch` / `curl` / 本地静态站）
4. 一个零依赖画廊生成器 `build_gallery.py`（整幅 hero + 照片墙 + 键盘/触屏灯箱）
5. 一次完整的实战对话、验收清单、排错速查

## 重要

使用前请先读 [`DISCLAIMER.md`](./DISCLAIMER.md)。本教程面向**个人存档**场景，
照片版权归拍摄者所有，仅供个人查看，不得二次分发或商用；只处理公开可达的内容，
不绕过任何访问控制。

## 许可

文字与代码以 [MIT](./LICENSE) 许可发布，可自由使用、修改、再分发。
**照片不在 MIT 覆盖范围内**：`photos/` 下的图片版权归各拍摄者所有，仅供个人查看，
详情见 [`DISCLAIMER.md`](./DISCLAIMER.md)。
