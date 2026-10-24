// Runs automatically after every successful Netlify deploy.
// Tells IndexNow (Bing, Yandex, Seznam, Naver and others) which pages changed:
// the front page, the section pages and every article from the last 48 hours.
import { readFileSync } from "node:fs";

const SITE = "https://latinogazette.com";
const SECTIONS = ["nation", "politics", "elections", "business", "communities", "culture", "opinion", "wellbeing"];

export const handler = async (event) => {
  let deploy = {};
  try { deploy = JSON.parse(event.body || "{}").payload || {}; } catch (e) {}
  if (deploy.context && deploy.context !== "production") {
    return { statusCode: 200, body: "skipped: not production" };
  }
  const key = process.env.INDEXNOW_KEY || JSON.parse(readFileSync(new URL("../../site.json", import.meta.url))).indexnow_key;
  const host = new URL(SITE).host;

  let recent = [];
  try {
    const xml = await fetch(`${SITE}/news-sitemap.xml`, { cache: "no-store" }).then((r) => r.text());
    recent = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
  } catch (e) {}

  const urlList = [...new Set([`${SITE}/`, ...SECTIONS.map((s) => `${SITE}/${s}/`), `${SITE}/election-night/`, ...recent])];
  const res = await fetch("https://api.indexnow.org/indexnow", {
    method: "POST",
    headers: { "content-type": "application/json; charset=utf-8" },
    body: JSON.stringify({ host, key, keyLocation: `${SITE}/${key}.txt`, urlList }),
  });
  console.log(`IndexNow: ${res.status} for ${urlList.length} URLs`);
  return { statusCode: 200, body: `IndexNow ${res.status}` };
};
