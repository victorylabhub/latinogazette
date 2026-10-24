#!/usr/bin/env python3
"""Latino Gazette — static site generator.

Usage:  python3 build.py   → writes dist/
Settings: site.json · Sections: SECTIONS below · Articles: content/articles/*.md
Pages: content/pages/*.md · Election data: data/*.json
"""
import datetime as dt
import hashlib
import json
import shutil
from email.utils import format_datetime
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
ET = dt.timezone(dt.timedelta(hours=-5))
env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
SITE["v"] = hashlib.md5(b"".join((ROOT / "static" / f).read_bytes()
                                 for f in ("site.css", "site.js"))).hexdigest()[:8]
SITE["year"] = dt.date.today().year

SECTIONS = [
    ("nation", "Nation", "National news and policy through the lens of Latino communities."),
    ("politics", "Politics", "Campaigns, Congress, statehouses and the people shaping policy."),
    ("elections", "Elections", "The 2026 election: how to vote, what's on the ballot and official results."),
    ("business", "Business", "Entrepreneurs, workers, wages and the economics of opportunity."),
    ("communities", "Communities", "Neighborhoods, families and local life across the country."),
    ("culture", "Culture", "Arts, music, food, faith, sports and identity."),
    ("opinion", "Opinion", "Signed commentary and analysis. Opinion pieces reflect the views of their authors."),
    ("wellbeing", "Wellbeing", "Health, education, housing and the conditions for a good life."),
]
SECTION = {k: {"slug": k, "name": n, "desc": d} for k, n, d in SECTIONS}

STATES = [
    ("al", "Alabama"), ("ak", "Alaska"), ("az", "Arizona"), ("ar", "Arkansas"),
    ("ca", "California"), ("co", "Colorado"), ("ct", "Connecticut"), ("de", "Delaware"),
    ("dc", "District of Columbia"), ("fl", "Florida"), ("ga", "Georgia"), ("hi", "Hawaii"),
    ("id", "Idaho"), ("il", "Illinois"), ("in", "Indiana"), ("ia", "Iowa"), ("ks", "Kansas"),
    ("ky", "Kentucky"), ("la", "Louisiana"), ("me", "Maine"), ("md", "Maryland"),
    ("ma", "Massachusetts"), ("mi", "Michigan"), ("mn", "Minnesota"), ("ms", "Mississippi"),
    ("mo", "Missouri"), ("mt", "Montana"), ("ne", "Nebraska"), ("nv", "Nevada"),
    ("nh", "New Hampshire"), ("nj", "New Jersey"), ("nm", "New Mexico"), ("ny", "New York"),
    ("nc", "North Carolina"), ("nd", "North Dakota"), ("oh", "Ohio"), ("ok", "Oklahoma"),
    ("or", "Oregon"), ("pa", "Pennsylvania"), ("ri", "Rhode Island"), ("sc", "South Carolina"),
    ("sd", "South Dakota"), ("tn", "Tennessee"), ("tx", "Texas"), ("ut", "Utah"),
    ("vt", "Vermont"), ("va", "Virginia"), ("wa", "Washington"), ("wv", "West Virginia"),
    ("wi", "Wisconsin"), ("wy", "Wyoming"),
]
STATE_NAME = dict(STATES)
MONTHS = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.",
          "Nov.", "Dec."]
MONTHS_FULL = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def ap_date(d):
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def long_date(d):
    return f"{WEEKDAYS[d.weekday()]}, {MONTHS_FULL[d.month - 1]} {d.day}, {d.year}"


env.filters["apdate"] = ap_date
env.filters["longdate"] = long_date


def to_dt(d):
    if d is None:
        return None
    if isinstance(d, str):
        d = dt.datetime.fromisoformat(d.replace("Z", "+00:00"))
    if isinstance(d, dt.date) and not isinstance(d, dt.datetime):
        d = dt.datetime(d.year, d.month, d.day, 9)
    if d.tzinfo is None:
        d = d.replace(tzinfo=ET)
    return d.astimezone(ET)


def read_md(f):
    raw = f.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return None, raw
    _, head, body = raw.split("---", 2)
    return (yaml.safe_load(head) or {}), body.strip()


MD = ["extra", "sane_lists", "smarty"]


def load_articles():
    out = []
    for f in sorted((ROOT / "content" / "articles").glob("*.md")):
        m, body = read_md(f)
        if not m or m.get("draft") or m.get("section") not in SECTION:
            continue
        # Publication rules: signed, dated, with at least one linked source.
        if not m.get("author") or not m.get("date"):
            print(f"! skipped {f.name}: needs author and date")
            continue
        m["date"] = to_dt(m["date"])
        m["updated"] = to_dt(m.get("updated"))
        m["slug"] = f.stem
        m["sec"] = SECTION[m["section"]]
        m["url"] = f"/{m['section']}/{f.stem}/"
        m["html"] = markdown.markdown(body, extensions=MD)
        m["minutes"] = max(1, round(len(body.split()) / 230))
        m["sources"] = [s for s in (m.get("sources") or []) if s.get("url")]
        out.append(m)
    out.sort(key=lambda a: a["date"], reverse=True)
    return out


def load_pages():
    pages = {}
    for f in sorted((ROOT / "content" / "pages").glob("*.md")):
        m, body = read_md(f)
        m = m or {}
        m["slug"] = f.stem
        m["html"] = markdown.markdown(body, extensions=MD + ["toc"])
        m["updated"] = to_dt(m.get("updated"))
        pages[f.stem] = m
    return pages


def load_json(name, default):
    f = ROOT / "data" / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else default


def write(path, html):
    p = DIST / path.strip("/") / "index.html" if path.strip("/") else DIST / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")


def esc(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def homepage(arts):
    """Assign articles to home slots without repeating any story."""
    used = set()

    def take(pred, n):
        got = [a for a in arts if a["slug"] not in used and pred(a)][:n]
        used.update(a["slug"] for a in got)
        return got

    news = lambda a: a["section"] != "opinion"
    lead = take(lambda a: news(a) and a.get("featured"), 1) or take(news, 1)
    side = take(news, 4)
    long_read = take(lambda a: a.get("long_read") and a.get("image"), 1)
    opinion = take(lambda a: a["section"] == "opinion", 4)
    latest = take(news, 4)
    rows = []
    for slug, name, _ in SECTIONS:
        if slug == "opinion":
            continue
        got = take(lambda a, s=slug: a["section"] == s, 4)
        if got:
            rows.append((SECTION[slug], got))
    return dict(lead=lead[0] if lead else None, side=side, long_read=long_read[0] if long_read else None,
                opinion=opinion, latest=latest, rows=rows)


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    arts = load_articles()
    pages = load_pages()
    closing = load_json("poll_closing.json", {})
    results = load_json("results_urls.json", {})
    hotlines = load_json("hotlines.json", [])

    today = dt.datetime.now(ET).date()
    eday = dt.date.fromisoformat(SITE["election_date"])
    SITE["elections_on"] = today <= dt.date.fromisoformat(SITE["show_elections_until"])
    SITE["days_to_election"] = (eday - today).days
    SITE["today"] = today

    common = dict(site=SITE, sections=[SECTION[k] for k, _, _ in SECTIONS])
    render = lambda tpl, **kw: env.get_template(tpl).render(**common, **kw)
    urls = ["/"]

    write("/", render("home.html", page="home", **homepage(arts),
                      has_articles=bool(arts)))

    for slug, name, desc in SECTIONS:
        sel = [a for a in arts if a["section"] == slug]
        write(f"/{slug}/", render("section.html", page=slug, sec=SECTION[slug], items=sel,
                                  title=name, lede=desc))
        urls.append(f"/{slug}/")

    for a in arts:
        related = [r for r in arts if r is not a and r["section"] == a["section"]][:4]
        write(a["url"], render("article.html", page=a["section"], a=a, related=related,
                               title=a["title"], lede=a.get("dek", "")))
        urls.append(a["url"])

    # Election service pages (official sources only)
    groups = []
    for g in closing.get("groups", []):
        names = sorted(STATE_NAME[c] for c in g["states"] if c in closing.get("states", {}))
        if names:
            groups.append({"et": g["et"], "names": names})
    later = [(STATE_NAME[c], s["last_et"]) for c, s in sorted(closing.get("states", {}).items(),
                                                            key=lambda x: STATE_NAME[x[0]])
             if s.get("last_et") and s["last_et"] != s.get("most_et")]
    res = sorted(((STATE_NAME[c], r["url"]) for c, r in results.get("states", {}).items()
                  if c in STATE_NAME and r.get("url")), key=lambda x: x[0])
    local = [(STATE_NAME[l["state"]], l["text"]) for l in closing.get("local", [])]
    write("/election-night/", render(
        "election_night.html", page="elections", groups=groups, later=later, results=res, local=local,
        hotlines=hotlines, title="Election night 2026",
        lede="Poll closing times and links to every state's official results for the Nov. 3 general election."))
    write("/how-to-vote/", render(
        "how_to_vote.html", page="elections", states=STATES, hotlines=hotlines,
        title="How to vote on Nov. 3, 2026",
        lede="Rules vary by state. Every step below points to an official government source."))
    urls += ["/election-night/", "/how-to-vote/"]

    for slug, pg in pages.items():
        write(f"/{slug}/", render("page.html", page=slug, pg=pg, title=pg.get("title", slug),
                                  lede=pg.get("description", "")))
        urls.append(f"/{slug}/")

    write("/newsletter/thanks/", render(
        "page.html", page="newsletter", title="You're signed up", lede="",
        pg={"title": "You're signed up", "html": "<p>Thank you for subscribing to The Gazette Brief. "
            f"You can unsubscribe at any time by writing to <a href=\"mailto:{SITE['privacy_email']}\">"
            f"{SITE['privacy_email']}</a> or using the link in any email.</p>"
            "<p><a href=\"/\">Back to the front page</a></p>"}))

    (DIST / "404.html").write_text(render(
        "page.html", page="404", title="Page not found", lede="",
        pg={"title": "Page not found", "html": "<p>This address doesn't exist or has moved. "
            "<a href=\"/\">Go to the front page</a>.</p>"}), encoding="utf-8")

    shutil.copytree(ROOT / "static", DIST / "static")
    shutil.copytree(ROOT / "admin", DIST / "admin")

    base = f"https://{SITE['domain']}"
    items = "".join(
        f"<item><title>{esc(a['title'])}</title><link>{base}{a['url']}</link>"
        f"<guid>{base}{a['url']}</guid><pubDate>{format_datetime(a['date'])}</pubDate>"
        f"<dc:creator>{esc(a['author'])}</dc:creator>"
        f"<description>{esc(a.get('dek', ''))}</description></item>" for a in arts[:40])
    (DIST / "rss.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>'
        f"<title>Latino Gazette</title><link>{base}/</link><description>{esc(SITE['description'])}"
        f"</description><language>en-us</language>{items}</channel></rss>", encoding="utf-8")
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{base}{u}</loc></url>\n" for u in urls) + "</urlset>\n",
        encoding="utf-8")
    recent = [a for a in arts if (dt.datetime.now(ET) - a["date"]).days < 2]
    (DIST / "news-sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        + "".join(f"  <url><loc>{base}{a['url']}</loc><news:news><news:publication><news:name>Latino Gazette</news:name>"
                  f"<news:language>en</news:language></news:publication><news:publication_date>{a['date'].isoformat()}"
                  f"</news:publication_date><news:title>{esc(a['title'])}</news:title></news:news></url>\n" for a in recent)
        + "</urlset>\n", encoding="utf-8")
    noindex = SITE.get("noindex")
    (DIST / "robots.txt").write_text(
        ("User-agent: *\nDisallow: /\n" if noindex else "User-agent: *\nDisallow: /admin/\n")
        + f"Sitemap: {base}/sitemap.xml\nSitemap: {base}/news-sitemap.xml\n", encoding="utf-8")
    print(f"✓ dist/ ready: {len(urls)} pages, {len(arts)} articles, {len(res)} results links, "
          f"{len(groups)} closing groups")


if __name__ == "__main__":
    build()
