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
    wall.style.setProperty('--cols', cols);
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
