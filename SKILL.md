# Concert Photo Gallery

Build a photo collection and gallery website for a K-pop idol at a specific concert or event, from the user's one-line ask (idol name, optionally a concert or date) to delivered photos or a shared gallery URL.

## Identify the subject and event

- Parse the ask for three things: the idol (name, group), the event (tour or concert name), and the date. Any of them may be missing.

- When the user names only the idol, default to recent stage photos from the last year and say so. When they give a bare date like 20260321, confirm what event falls on it with `browser.search` before collecting.

- Verify the event with one search: tour name, date, venue, city. Keep the verified facts for captions and file names.

## Find the photos

- Search with `/opt/hatch/bin/image-search`, not the generic web search. Run several phrasings per target: English (`Leeseo IVE DIVE INTO IVE fan concert day 1`), Chinese (`李瑞 2026 仁川 粉丝演唱会`), and date variants (`260321`, `2026-03-21`). Pass `--max-results 25`.

- From each result keep `media_url` as the download locator and `page_url` for provenance. Filter results by `page_url`: keep only ones whose page is about the target event. Prefer photos whose page or filename carries the event date.

- When the user wants every photo from one gallery page (for example a kpopping gallery showing "Photo 1 of 25"), fetch the page and collect the direct image URLs. Static HTML often embeds only the first photos; the rest load through the page's viewer. In that case spawn a `browser.spawn_task` that clicks through every photo in the viewer and reports each direct `cdn.*` image URL. Never guess URL patterns.

## Download and verify

- Download one candidate at a time with bounded timeouts and browser-like headers:

```sh
curl -fsSL --connect-timeout 10 --max-time 60 -A 'Mozilla/5.0' \
  -H 'Referer: https://www.google.com/' -o '<dest>' '<media_url>'
```

- Run `file` on every download and keep only real JPEG/PNG/WebP bytes. Drop 404s, HTML error pages, and hotlink-blocked hosts without retrying more than once.

- Save to `~/workspace/<idol>-photos/<yyyymmdd>-<event>/` with sequential names (`photo-1.jpg`, ...). Deduplicate by URL before downloading.

## Deliver

- For a handful of photos, attach them directly in chat, one per line: `![alt](sandbox://workspace/<path>)`.

- For a full set, zip the folder and attach the zip on its own line.

- For a gallery website, call `artifact.create_web_static` with the user's exact words in `verbatim_request`, a factual `icon_subject`, and `capabilities` `{"connectors": [], "public_web_read": false}`. The builder ingests the downloaded photos from the workspace folder. When the user asked for a URL, call `artifact.share` after the build succeeds and hand them the returned URL.

- Credit the photos as fan-taken and for personal viewing only, in the reply or the gallery footer.

## Limits

- Image hosts go stale fast. A URL that 404s or 520s today is dead; move on to the next source instead of forcing it.

- Never present a guessed or reconstructed image URL as a real photo. Every delivered photo must be a byte-verified download or a builder-verified gallery render.

- The photos belong to their photographers. Package and share for the user's personal viewing, never for redistribution or commercial use.

- Only fetch pages and images the site already serves publicly. Never use request headers, proxies, or retries to defeat access controls, paywalls, or anti-scraping measures. If a host blocks the request, treat that source as unavailable and move on. Respect each site's terms of service and `robots.txt`, and prefer official or licensed sources.
