#!/usr/bin/env python3
"""Render blog.md into a self-contained index.html for GitHub Pages, and
publish the installable skill files into dist/.

    python3 -m pip install markdown
    python3 build.py                 # writes index.html + dist/
    python3 build.py --repo-url URL  # override the GitHub link in the footer
    python3 build.py --no-dist       # skip the dist/ sync
"""
import argparse
import html
import os
import re
import sys

try:
    import markdown
except ImportError:
    sys.exit("missing dependency: python3 -m pip install markdown")

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "blog.md")
OUTPUT = os.path.join(HERE, "index.html")
DIST = os.path.join(HERE, "dist", "pop")

DEFAULT_REPO = "https://github.com/Laotree/opencode-concert-gallery"

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="color-scheme" content="dark">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<link rel="stylesheet" href="./assets/style.css">
</head>
<body>

<header id="bar">
  <div class="brand">Concert Photo Gallery <span>·</span> OpenCode Skill 教程</div>
  <nav class="links">
    <a href="{repo}">GitHub</a>
    <a href="{repo}/blob/main/DISCLAIMER.md">使用边界</a>
  </nav>
</header>
<div id="progress"></div>

<div class="wrap">
<main>
<article class="hero">
  <p class="kicker">OpenCode · Skill · 本地实战</p>
  <h1>{title}</h1>
  <p class="lede">{description}</p>
</article>

{body}

<footer>
  <p class="notice">{footer_notice}</p>
  <p>教程源码与技能本体：<a href="{repo}">{repo_short}</a> ·
     使用前请阅读 <a href="{repo}/blob/main/DISCLAIMER.md">使用边界</a>。</p>
  <p>文字与代码以 <a href="{repo}/blob/main/LICENSE">MIT</a> 许可发布；照片不在此列，版权归拍摄者所有。</p>
</footer>
</main>

<aside class="toc">
  <div class="toc-title">目录</div>
  {toc}
</aside>
</div>

<script src="./assets/app.js"></script>
</body>
</html>
"""


def read_source():
    with open(SOURCE, encoding="utf-8") as fh:
        return fh.read()


def split_title(text):
    """Take the first H1 out of the body so it can live in the hero."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            body = "\n".join(lines[i + 1:]).lstrip("\n")
            return title, body
    return "Concert Photo Gallery", text


def insert_toc_marker(text):
    """Put a `[TOC]` marker before the first H2 so mobile readers get an inline TOC."""
    for i, line in enumerate(text.split("\n")):
        if line.startswith("## "):
            lines = text.split("\n")
            lines.insert(i, "[TOC]\n")
            return "\n".join(lines)
    return text


def slugify(value, separator):
    """CJK-friendly heading slug: keeps unicode word chars, drops emoji/punctuation."""
    value = value.strip().lower()
    value = re.sub(r"[\s\./]+", separator, value)
    value = re.sub(r"[^\w\-%s]" % re.escape(separator), "", value, flags=re.UNICODE)
    value = re.sub(r"%s+" % re.escape(separator), separator, value)
    return value.strip(separator)


def render(body):
    md = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists"],
        extension_configs={
            "toc": {"toc_depth": "2-3", "anchorlink": False, "slugify": slugify}
        },
    )
    out = md.convert(insert_toc_marker(body))
    # md.toc keeps its own <div class="toc"> wrapper; the sidebar supplies its own.
    toc = re.sub(r'^\s*<div class="toc">\s*', "", md.toc)
    toc = re.sub(r"\s*</div>\s*$", "", toc)
    return out, toc


def polish(html_text):
    """Turn `- [ ] foo` lines into real checkboxes and tidy the TOC class."""
    html_text = re.sub(
        r"<li>\[ \]\s*", '<li class="task"><span class="box"></span>', html_text
    )
    return html_text


def extract_skill(text):
    """Pull the two installable artefacts out of blog.md.

    blog.md is the single source of truth: the ````markdown block holds the
    full SKILL.md (frontmatter included) and the ```python block holds
    build_gallery.py. install.sh fetches them from dist/.
    """
    skill_m = re.search(r"^````markdown\n(.*?)\n````\s*$", text, re.S | re.M)
    script_m = re.search(r"^```python\n(.*?)\n```\s*$", text, re.S | re.M)
    if not skill_m or not script_m:
        sys.exit("blog.md: could not find the ``````markdown / ```python blocks")
    skill, script = skill_m.group(1) + "\n", script_m.group(1) + "\n"

    head = skill.split("---", 2)
    if not skill.startswith("---\n") or len(head) < 3 or "description:" not in head[1]:
        sys.exit("blog.md: SKILL.md block is missing frontmatter (name/description)")
    if not script.startswith("#!/usr/bin/env python3"):
        sys.exit("blog.md: the python block does not look like build_gallery.py")
    return skill, script


def sync_dist(text):
    """Write dist/pop/{SKILL.md,scripts/build_gallery.py}."""
    skill, script = extract_skill(text)
    files = {
        os.path.join(DIST, "SKILL.md"): (skill, 0o644),
        os.path.join(DIST, "scripts", "build_gallery.py"): (script, 0o755),
    }
    for path, (content, mode) in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.chmod(path, mode)
    rel = os.path.relpath(DIST, HERE)
    print("synced %s/ (%d + %d bytes)" % (rel, len(skill), len(script)))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-url", default=DEFAULT_REPO)
    ap.add_argument("--out", default=OUTPUT)
    ap.add_argument("--no-dist", action="store_true", help="skip the dist/ sync")
    args = ap.parse_args()

    source = read_source()
    title, body = split_title(source)
    rendered, toc = render(body)
    if not args.no_dist:
        sync_dist(source)

    description = (
        "用 OpenCode V2 的 Skill 在本机搭建演唱会照片画廊：安装、加载技能、"
        "适配本地工具、生成静态画廊站点，附完整脚本与排错清单。"
    )
    footer_notice = (
        "照片版权归拍摄者所有，本教程仅面向个人存档：仅供个人查看，不得二次分发或商用；"
        "只处理公开可达的内容，不绕过任何访问控制。"
    )

    doc = TEMPLATE.format(
        title=html.escape(title),
        description=html.escape(description),
        body=polish(rendered),
        toc=toc,
        repo=args.repo_url,
        repo_short=args.repo_url.replace("https://github.com/", ""),
        footer_notice=footer_notice,
    )

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print("wrote %s (%d KB)" % (args.out, len(doc) // 1024))


if __name__ == "__main__":
    main()
