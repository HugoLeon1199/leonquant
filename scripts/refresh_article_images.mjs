/**
 * Bổ sung image_url cho allArticles trong content.json khi không chạy được Python.
 * Fetch HTML từng bài, đọc og/twitter meta, JSON-LD, <img>, hoặc URL ảnh trong summary.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");

const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 LEONQuantLabs/1.0";
const MAX_BYTES = 450_000;
const IMG_SLICE = 400_000;

const SKIP_SUB = [
  "pixel",
  "tracking",
  "1x1",
  "spacer",
  "blank.gif",
  "transparent",
  "analytics",
  "emoji",
  "favicon",
  "/icon",
  "logo-small",
];

function normalizeMediaUrl(pageUrl, raw) {
  let u = (raw || "").trim();
  if (!u || u.startsWith("data:")) return "";
  u = u.replace(/&amp;/g, "&");
  if (u.startsWith("//")) u = "https:" + u;
  try {
    const abs = new URL(u, pageUrl);
    u = abs.href;
  } catch {
    return "";
  }
  const low = u.toLowerCase();
  if (SKIP_SUB.some((s) => low.includes(s))) return "";
  return u;
}

function attr(tag, qname) {
  const re = new RegExp(
    `(?:^|\\s)${qname}\\s*=\\s*["']([^"']*)["']`,
    "i",
  );
  const m = tag.match(re);
  return m ? m[1] : "";
}

function extractFromMetas(html, pageUrl) {
  const re = /<meta\s+[^>]*>/gi;
  let m;
  const imageProps = new Set([
    "og:image",
    "og:image:url",
    "og:image:secure_url",
    "twitter:image",
  ]);
  while ((m = re.exec(html))) {
    const tag = m[0];
    const content = attr(tag, "content");
    if (!content) continue;
    const prop = attr(tag, "property").toLowerCase();
    const name = attr(tag, "name").toLowerCase();
    const itemprop = attr(tag, "itemprop").toLowerCase();
    if (imageProps.has(prop)) {
      const nu = normalizeMediaUrl(pageUrl, content);
      if (nu) return nu;
    }
    if (
      ["twitter:image", "twitter:image:src", "thumbnail"].includes(name)
    ) {
      const nu = normalizeMediaUrl(pageUrl, content);
      if (nu) return nu;
    }
    if (itemprop === "image") {
      const nu = normalizeMediaUrl(pageUrl, content);
      if (nu) return nu;
    }
  }
  return "";
}

function extractFromLinks(html, pageUrl) {
  const re = /<link\s+[^>]*>/gi;
  let m;
  while ((m = re.exec(html))) {
    const tag = m[0];
    const rel = attr(tag, "rel").toLowerCase();
    const asVal = attr(tag, "as").toLowerCase();
    const href = attr(tag, "href");
    if (!href) continue;
    if (rel === "image_src") {
      const nu = normalizeMediaUrl(pageUrl, href);
      if (nu) return nu;
    }
    if (rel === "preload" && asVal === "image") {
      const nu = normalizeMediaUrl(pageUrl, href);
      if (nu) return nu;
    }
  }
  return "";
}

function extractJsonLdImages(html, pageUrl) {
  const re =
    /<script[^>]+type\s*=\s*["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let lm;
  while ((lm = re.exec(html))) {
    const blob = lm[1];
    if (!/image/i.test(blob)) continue;
    const r1 = /"image"\s*:\s*"([^"]+)"/i.exec(blob);
    if (r1) {
      const nu = normalizeMediaUrl(pageUrl, r1[1]);
      if (nu) return nu;
    }
    const r2 = /"image"\s*:\s*\[\s*"([^"]+)"/i.exec(blob);
    if (r2) {
      const nu = normalizeMediaUrl(pageUrl, r2[1]);
      if (nu) return nu;
    }
  }
  return "";
}

function extractImgTags(html, pageUrl) {
  const slice = html.slice(0, IMG_SLICE);
  const imgRe =
    /<img\b[^>]*?\b(?:src|data-src|data-original|data-lazy-src)\s*=\s*["']([^"'\s>]+)["']/gi;
  let im;
  while ((im = imgRe.exec(slice))) {
    const nu = normalizeMediaUrl(pageUrl, im[1]);
    if (nu) return nu;
  }
  return "";
}

function extractFromPlaintext(text) {
  const re =
    /https?:\/\/[^\s"'<>]+\.(?:jpg|jpeg|png|webp|gif)(?:\?[^\s"'<>]*)?/gi;
  const slice = (text || "").slice(0, 50_000);
  let m;
  while ((m = re.exec(slice))) {
    const u = m[0];
    const low = u.toLowerCase();
    if (SKIP_SUB.some((s) => low.includes(s))) continue;
    return u;
  }
  return "";
}

function pickImage(html, pageUrl, summary) {
  const order = [
    () => extractFromMetas(html, pageUrl),
    () => extractFromLinks(html, pageUrl),
    () => extractJsonLdImages(html, pageUrl),
    () => extractImgTags(html, pageUrl),
  ];
  for (const fn of order) {
    const u = fn();
    if (u) return u;
  }
  return extractFromPlaintext(summary);
}

async function fetchImageForArticle(url, summary, timeoutMs) {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: ac.signal,
      headers: {
        "User-Agent": UA,
        Accept: "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
      },
      redirect: "follow",
    });
    if (!res.ok)
      return {
        image_url: "",
        metadata_status: `http_${res.status}`,
      };
    const buf = await res.arrayBuffer();
    const chunk =
      buf.byteLength > MAX_BYTES ? buf.slice(0, MAX_BYTES) : buf;
    const html = new TextDecoder("utf-8", { fatal: false }).decode(chunk);
    const image_url = pickImage(html, url, summary);
    return {
      image_url: image_url || "",
      metadata_status: image_url ? "ok" : "no_image",
    };
  } catch {
    return { image_url: "", metadata_status: "error" };
  } finally {
    clearTimeout(t);
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function main() {
  const args = process.argv.slice(2);
  let timeoutMs = 14_000;
  let delayMs = 400;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--timeout" && args[i + 1])
      timeoutMs = parseInt(args[++i], 10) || timeoutMs;
    if (args[i] === "--delay" && args[i + 1])
      delayMs = parseInt(args[++i], 10) || delayMs;
  }

  const contentPath = path.join(root, "content.json");
  const content = JSON.parse(fs.readFileSync(contentPath, "utf8"));
  const articles = Array.isArray(content.allArticles) ? content.allArticles : [];
  let updated = 0;
  for (let i = 0; i < articles.length; i++) {
    const art = articles[i];
    const url = art.url;
    if (!url || typeof url !== "string") continue;
    const hasImage = (art.image_url || "").trim().length > 0;
    if (hasImage && art.metadata_status === "ok") continue;

    process.stderr.write(`[${i + 1}/${articles.length}] ${url.slice(0, 60)}…\n`);
    const { image_url, metadata_status } = await fetchImageForArticle(
      url,
      art.summary || "",
      timeoutMs,
    );
    if (image_url) {
      art.image_url = image_url;
      updated++;
    }
    art.metadata_status = metadata_status;
    if (delayMs > 0) await sleep(delayMs);
  }

  fs.writeFileSync(contentPath, JSON.stringify(content, null, 2), "utf8");
  process.stderr.write(`Done. Filled ${updated} image_url field(s).\n`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
