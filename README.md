# Latino Gazette (latinogazette.com)

Digital news publication of Atlas Media Network, LLC. Static site generated with Python (Jinja2 + Markdown), newsroom on Decap CMS at `/admin/`, hosted on Netlify (team "Victory build", project `latinogazette`).

## How it works
- `build.py` reads `site.json`, `content/` and `data/` and writes the site to `dist/`.
- Netlify runs the build on every push to `main` (see `netlify.toml`).
- Articles: `content/articles/*.md`, created from `/admin/`. URL: `/<section>/<file-name>/`.
- Fixed pages: `content/pages/*.md` (About, Standards, Corrections, Contact, Privacy).
- Elections: `data/poll_closing.json`, `data/results_urls.json`, `data/hotlines.json`. Each entry records its official source.

## Publishing rules
- Every article needs a byline, a date and at least one linked source (the newsroom enforces this).
- Drafts stay on their own branch (editorial workflow) until an editor publishes them; publishing merges into `main`.
- The front page fills itself: lead story (or the one marked "Lead story"), four side stories, Latest, The Long Read, Opinion and one row per section.
- The election module and the election bar show until `show_elections_until` in `site.json`.

## Local preview
```
pip install -r requirements.txt
python3 build.py
cd dist && python3 -m http.server 8000
```

## Newsroom (Decap CMS) setup
The newsroom signs in with GitHub through Netlify:
1. GitHub → Settings → Developer settings → OAuth Apps → New: Homepage `https://latinogazette.com`, callback `https://api.netlify.com/auth/done`.
2. Netlify → latinogazette → Project configuration → Access & security → OAuth → Install provider → GitHub, paste Client ID and Secret.
3. Editors need write access to `victorylabhub/latinogazette`.

## Pending
- Privacy notice: legal review.
- Newsletter: sign-ups are collected by Netlify Forms (form "newsletter"); connect a sending service before the first issue.
