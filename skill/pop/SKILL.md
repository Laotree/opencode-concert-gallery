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
