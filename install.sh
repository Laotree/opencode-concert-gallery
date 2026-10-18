#!/usr/bin/env bash
# One-shot installer for the "pop" OpenCode skill (concert_photo_gallery).
#
#   curl -fsSL https://laotree.github.io/opencode-concert-gallery/install.sh | bash
#
# Checks the environment, installs OpenCode V2 if missing, and downloads the
# skill + gallery builder into <dir>/.opencode/skills/pop/.
# No git required. Idempotent: safe to re-run, it overwrites the skill files.
set -euo pipefail

REPO="Laotree/opencode-concert-gallery"
# the skill lives in the repo at skill/pop/ and is published to Pages by CI
BASE="${SKILL_BASE:-https://laotree.github.io/opencode-concert-gallery}"
DIST="skill/pop"
DIR="${HOME}/concert-photo-gallery"
SKILLS_DIR=".opencode/skills"
ID="pop"
WITH_OPENCODE=1
OPENCODE_INSTALL_URL="https://opencode.ai/v2/install"

if [ -t 1 ]; then
  B=$'\033[1m'; DIM=$'\033[2m'; R=$'\033[0m'
  G=$'\033[32m'; Y=$'\033[33m'; E=$'\033[31m'; C=$'\033[36m'
else
  B=""; DIM=""; R=""; G=""; Y=""; E=""; C=""
fi
say()  { printf '%s\n' "$*"; }
ok()   { printf '  %s✔%s %s\n' "$G" "$R" "$*"; }
warn() { printf '  %s!%s %s\n' "$Y" "$R" "$*"; }
die()  { printf '  %s✘%s %s\n' "$E" "$R" "$*" >&2; exit 1; }
step() { printf '\n%s▸ %s%s\n' "$B" "$*" "$R"; }

usage() {
  cat <<EOF
${B}pop${R} installer${DIM}  (concert_photo_gallery)${R}

  ./install.sh [options]

Options:
  --dir DIR          project folder to create (default: ~/concert-photo-gallery)
  --skills-dir DIR   skill root inside it (default: .opencode/skills)
  --id NAME          skill folder name = the @id you type (default: pop)
  --base URL         raw base URL to download from (default: the published repo)
  --no-opencode      do not install OpenCode, only fetch the skill
  --local PATH       copy the skill from a local checkout (e.g. skill/pop) instead of the network
  -h, --help         this help

  curl -fsSL ${C}https://laotree.github.io/opencode-concert-gallery/install.sh${R} | bash
  ... | bash -s -- --dir ~/my-gallery --no-opencode
EOF
}

LOCAL_SRC=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dir)         DIR="$2"; shift 2 ;;
    --skills-dir)  SKILLS_DIR="$2"; shift 2 ;;
    --id)          ID="$2"; shift 2 ;;
    --base)        BASE="$2"; shift 2 ;;
    --no-opencode) WITH_OPENCODE=0; shift ;;
    --local)       LOCAL_SRC="$2"; shift 2 ;;
    -h|--help)     usage; exit 0 ;;
    *)             die "unknown option: $1 (try --help)" ;;
  esac
done

DIR="${DIR/#\~/$HOME}"
DEST="$DIR/$SKILLS_DIR/$ID"

say ""
say "${B}Concert Photo Gallery · 一键安装${R}"
say "${DIM}技能装到 ${DEST}${R}"

# ---------------------------------------------------------------- 1. platform
step "1/4  检查环境"
case "$(uname -s 2>/dev/null || echo unknown)" in
  Darwin) OS="macOS" ;;
  Linux)  OS="Linux" ;;
  *)      OS="$(uname -s 2>/dev/null || echo unknown)" ;;
esac
ARCH="$(uname -m 2>/dev/null || echo unknown)"
ok "系统 ${OS} · ${ARCH}"

if command -v curl >/dev/null 2>&1; then
  DL="curl"; ok "curl $(curl --version | head -1 | awk '{print $2}')"
elif command -v wget >/dev/null 2>&1; then
  DL="wget"; ok "wget 可用"
else
  die "需要 curl 或 wget 才能下载（macOS/Linux 一般自带 curl）"
fi

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info>=(3,0) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -n "$PY" ]; then
  ok "$PY $("$PY" -c 'import platform;print(platform.python_version())')"
else
  warn "没找到 python3 —— 画廊生成器需要它（技能和 OpenCode 仍会装好）"
  say "     ${DIM}macOS: brew install python  ·  Debian/Ubuntu: sudo apt install python3${R}"
fi

# ---------------------------------------------------------------- 2. opencode
step "2/4  检查 OpenCode V2"
if [ "$WITH_OPENCODE" -eq 0 ]; then
  warn "已按 --no-opencode 跳过"
else
  HAVE=""
  if command -v opencode >/dev/null 2>&1; then
    HAVE="$(opencode --version 2>/dev/null || true)"
  fi
  if printf '%s' "$HAVE" | grep -Eq 'v?2\.'; then
    ok "已安装：${HAVE}"
  else
    [ -n "$HAVE" ] && warn "检测到旧版本（${HAVE}），将安装 V2"
    say "  ${DIM}→ ${OPENCODE_INSTALL_URL}${R}"
    if [ "$DL" = "curl" ]; then
      curl -fsSL "$OPENCODE_INSTALL_URL" | bash || {
        if command -v brew >/dev/null 2>&1; then
          warn "官方脚本失败，改用 Homebrew"
          brew install anomalyco/tap/opencode-v2
        else
          die "OpenCode 安装失败，请手动安装：https://opencode.ai/v2/docs/"
        fi
      }
    else
      wget -qO- "$OPENCODE_INSTALL_URL" | bash || die "OpenCode 安装失败，请手动安装"
    fi
    if command -v opencode >/dev/null 2>&1; then
      ok "安装完成：$(opencode --version 2>/dev/null)"
    else
      warn "装好了但当前 shell 还没刷新 PATH —— 新开一个终端再试 opencode --version"
    fi
  fi
fi

# ---------------------------------------------------------------- 3. skill
step "3/4  下载技能文件"
mkdir -p "$DEST/scripts"
fetch() { # fetch <relative-path> <dest>
  if [ "$DL" = "curl" ]; then
    curl -fsSL --retry 2 --connect-timeout 15 "$1" -o "$2"
  else
    wget -q --tries=2 --timeout=15 -O "$2" "$1"
  fi
}
if [ -n "$LOCAL_SRC" ]; then
  SRC="${LOCAL_SRC%/}"
  [ -f "$SRC/SKILL.md" ] || die "--local 指向的目录里没有 SKILL.md"
  cp -f "$SRC/SKILL.md" "$DEST/SKILL.md"
  cp -f "$SRC/scripts/build_gallery.py" "$DEST/scripts/build_gallery.py"
  ok "从本地复制：$SRC"
else
  fetch "$BASE/$DIST/SKILL.md"                  "$DEST/SKILL.md"               || die "下载 SKILL.md 失败：$BASE/$DIST/SKILL.md"
  ok "SKILL.md"
  fetch "$BASE/$DIST/scripts/build_gallery.py"  "$DEST/scripts/build_gallery.py" || die "下载 build_gallery.py 失败"
  ok "scripts/build_gallery.py"
fi

# ---------------------------------------------------------------- 4. verify
step "4/4  校验"
grep -q '^description:' "$DEST/SKILL.md" || die "SKILL.md 缺少 description，模型不会自动发现它"
ok "frontmatter 含 description"
if [ -n "$PY" ]; then
  "$PY" -m py_compile "$DEST/scripts/build_gallery.py" && ok "build_gallery.py 语法通过"
  rm -rf "$DEST/scripts/__pycache__"
else
  warn "跳过语法校验（没有 python3）"
fi
[ -s "$DEST/SKILL.md" ] && [ -s "$DEST/scripts/build_gallery.py" ] || die "文件不完整"
ok "技能 ID：${B}${ID}${R}"

say ""
say "${G}${B}完成。${R}技能位置："
say "  ${C}${DEST}${R}"
say ""
say "${B}接下来${R}"
say "  1) ${DIM}cd ${DIR} && opencode${R}"
say "  2) 在 TUI 里按 ${B}/connect${R} 登录一个模型"
say "  3) 输入 ${B}@${ID} 帮我找 <偶像> <场次> 的照片并做成画廊${R}"
[ -n "$PY" ] && say "     ${DIM}（技能会自己下载图片、建画廊，再用 python3 -m http.server 预览）${R}"
say ""
say "  ${DIM}使用边界：仅供个人查看，不得二次分发或商用。${R}"
say "  ${DIM}详见 https://github.com/$REPO/blob/main/DISCLAIMER.md${R}"
say ""
