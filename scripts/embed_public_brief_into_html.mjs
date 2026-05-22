/**
 * Nhúng bản tin digest từ content.json vào HTML tĩnh (GitHub Pages).
 * Trang luôn ở chế độ multisector-digest; không còn pipeline GPT brief.
 *
 * Usage: node scripts/embed_public_brief_into_html.mjs <page.html> <content.json>
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ND = "—";

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatDateVi(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getHostName(u) {
  try {
    return new URL(u).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

function proseToBullets(text) {
  const raw = String(text || "").trim();
  if (!raw) return [];
  if (/^\s*[-•*]\s/m.test(raw)) {
    return raw
      .split(/\n+/)
      .map((ln) => ln.replace(/^\s*[-•*]\s+/, "").trim())
      .filter(Boolean);
  }
  const out = [];
  const paras = raw.includes("\n\n") ? raw.split(/\n\s*\n/) : [raw];
  for (const para of paras) {
    const p = para.replace(/\s+/g, " ").trim();
    if (!p) continue;
    const chunks = p.split(/(?<=[.!?…])\s+(?=["'“‘(A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯ0-9])/);
    const parts = chunks.length > 1 ? chunks : p.split(/(?<=[;])\s+/);
    for (const c of parts) {
      const t = c.trim();
      if (t.length >= 18) out.push(t);
    }
  }
  return out.length ? out : [raw];
}

function getDigestBullets(data, arrayKey, fallbackText) {
  const arr = data[arrayKey];
  if (Array.isArray(arr) && arr.length) {
    return arr.map((s) => String(s || "").trim()).filter(Boolean);
  }
  return proseToBullets(fallbackText);
}

function mergeOverviewBullets(exec, intl, vn) {
  const seen = new Set();
  const out = [];
  for (const list of [exec, intl, vn]) {
    for (const b of list) {
      const t = String(b || "").trim();
      if (!t) continue;
      const key = t.toLowerCase().slice(0, 80);
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(t);
    }
  }
  return out;
}

function sectorSlug(name) {
  return (
    "sector-" +
    String(name || "linh-vuc")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
  );
}

const DIGEST_FOUR_SECTORS = [
  { code: "finance", name: "Kinh tế & Tài chính" },
  { code: "tech", name: "Công nghệ & AI" },
  { code: "news", name: "Thời sự & Chính trị" },
  { code: "trends", name: "Xu hướng & Đời sống" },
];

function inferDigestSectorCode(name) {
  const n = String(name || "").toLowerCase();
  if (/công nghệ|cong nghe|\bai\b|khoa học|bán dẫn|viễn thông|tech|chip/.test(n)) return "tech";
  if (/chính trị|thời sự|ngoại giao|địa chính|quốc tế|iran|israel|ukraine/.test(n)) return "news";
  if (/xu hướng|đời sống|quan điểm|góc nhìn|xã hội|pháp luật|y tế|môi trường|thể thao|văn hóa/.test(n)) return "trends";
  if (/kinh tế|tài chính|chứng khoán|bất động|tiền ảo|crypto|ngân hàng|thị trường/.test(n)) return "finance";
  return "trends";
}

function normalizeSectorItems(s) {
  if (Array.isArray(s.items) && s.items.length) {
    return s.items
      .filter((it) => it && String(it.headline || "").trim())
      .map((it) => ({
        headline: String(it.headline || "").trim(),
        links: (Array.isArray(it.links) ? it.links : []).filter(
          (lk) => lk && String(lk.url || "").trim(),
        ),
      }));
  }
  const pts = Array.isArray(s.keyPoints) ? s.keyPoints : [];
  const links = Array.isArray(s.links) ? s.links : [];
  return pts
    .map((p) => String(p || "").trim())
    .filter(Boolean)
    .map((headline, i) => ({
      headline,
      links: links.slice(i, i + 1),
    }));
}

function ensureDigestSectors(data) {
  const raw =
    Array.isArray(data.digestSectors) && data.digestSectors.length
      ? data.digestSectors.filter((s) => s && typeof s === "object")
      : (Array.isArray(data.globalMacroDrivers) ? data.globalMacroDrivers : []).map((d) => ({
          name: d.title || "Lĩnh vực",
          summary: d.analysis || "",
          keyPoints: String(d.marketImpact || "")
            .split("\n")
            .map((x) => x.replace(/^•\s*/, "").trim())
            .filter(Boolean),
          links: [],
        }));
  const buckets = Object.fromEntries(
    DIGEST_FOUR_SECTORS.map(({ code, name }) => [code, { code, name, summary: "", items: [] }]),
  );
  for (const s of raw) {
    const code = String(s.code || "").trim().toLowerCase() || inferDigestSectorCode(s.name);
    const bucket = buckets[code] || buckets.trends;
    bucket.name = String(s.name || "").trim() || bucket.name;
    if (String(s.summary || "").trim()) {
      bucket.summary = bucket.summary
        ? `${bucket.summary} ${String(s.summary).trim()}`.slice(0, 600)
        : String(s.summary).trim();
    }
    bucket.items.push(...normalizeSectorItems(s));
  }
  const seen = new Set();
  return DIGEST_FOUR_SECTORS.map(({ code, name }) => {
    const b = buckets[code];
    const items = [];
    for (const it of b.items) {
      const key = it.headline.toLowerCase().slice(0, 120);
      if (seen.has(key)) continue;
      seen.add(key);
      items.push(it);
    }
    return { code, name: b.name || name, summary: b.summary, items };
  });
}

function buildProseBulletsHtml(items) {
  if (!items.length) return `<p>${escapeHtml(ND)}</p>`;
  let h = `<ul class="sector-points prose-bullets">`;
  for (const it of items) h += `<li>${escapeHtml(it)}</li>`;
  h += `</ul>`;
  return h;
}

function buildLinkRowsHtml(links) {
  if (!links.length) return `<p class="hint">Chưa có liên kết nguồn.</p>`;
  let h = `<ul class="link-rows">`;
  for (const L of links) {
    const u = String(L.url || "").trim();
    if (!u) continue;
    const title = escapeHtml(L.title || L.host || u);
    const meta = [L.source, L.host].filter(Boolean).join(" · ");
    h += `<li><a href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">${title}</a>`;
    if (meta) h += `<span class="link-meta">${escapeHtml(meta)}</span>`;
    h += `</li>`;
  }
  h += `</ul>`;
  return h;
}

function buildArticleImageLookup(data) {
  const map = new Map();
  const add = (url, img) => {
    const u = String(url || "").trim();
    const i = String(img || "").trim();
    if (u && i && !map.has(u)) map.set(u, i);
  };
  for (const a of Array.isArray(data.allArticles) ? data.allArticles : []) {
    add(a.url, a.image_url || a.imageUrl);
  }
  for (const a of Array.isArray(data.articleLinkIndex) ? data.articleLinkIndex : []) {
    add(a.url, a.image_url || a.imageUrl);
  }
  return map;
}

function buildNotableCardsHtml(notable, imageByUrl) {
  const items = (Array.isArray(notable) ? notable : [])
    .filter((a) => a && String(a.url || "").trim())
    .slice(0, 9);
  if (!items.length) {
    return `<p class="hint">Chưa có tin nổi bật trong bản digest hôm nay.</p>`;
  }
  let h = `<div class="notable-list">`;
  items.forEach((a, idx) => {
    const u = String(a.url || "").trim();
    const title = escapeHtml(a.title || u);
    const meta = escapeHtml(
      [a.source, a.host || getHostName(u)].filter(Boolean).join(" · "),
    );
    const img = String(a.imageUrl || a.image_url || imageByUrl.get(u) || "").trim();
    const rank = String(idx + 1).padStart(2, "0");
    h += `<a class="notable-item" href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">`;
    h += `<span class="notable-item-rank">${rank}</span>`;
    if (img) {
      h += `<span class="notable-item-thumb"><img src="${escapeHtml(img)}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.parentElement.remove()"></span>`;
    }
    h += `<span class="notable-item-body">`;
    h += `<span class="notable-item-title">${title}</span>`;
    if (meta) h += `<span class="notable-item-meta">${meta}</span>`;
    h += `</span></a>`;
  });
  h += `</div>`;
  return h;
}

function buildSectorBlockHtml(s, index) {
  const code = String(s.code || "").trim();
  const name = String(s.name || "").trim() || "Lĩnh vực";
  const id = sectorSlug(code || name);
  const items = normalizeSectorItems(s);
  const intro = String(s.summary || "").trim();
  let h = `<article class="sector-block" id="${id}">`;
  h += `<header class="sector-head"><span class="sector-num">${String(index + 1).padStart(2, "0")}</span>`;
  h += `<div class="sector-head-main">`;
  if (code) h += `<span class="sector-code">${escapeHtml(code)}</span>`;
  h += `<h3>${escapeHtml(name)}</h3></div></header><div class="sector-body">`;
  if (intro) h += `<p class="sector-intro">${escapeHtml(intro)}</p>`;
  if (items.length) {
    h += `<ol class="sector-topic-list">`;
    items.forEach((it, ti) => {
      const lk = (it.links || [])[0];
      const u = lk ? String(lk.url || "").trim() : "";
      h += `<li class="sector-topic-row">`;
      h += `<span class="sector-topic-num">${String(ti + 1).padStart(2, "0")}</span>`;
      h += `<div class="sector-topic-main">`;
      h += `<p class="sector-topic-headline">${escapeHtml(it.headline)}</p>`;
      if (u) {
        h += `<a class="sector-topic-source" href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">Bấm vào đây xem tin liên quan</a>`;
      }
      h += `</div></li>`;
    });
    h += `</ol>`;
  } else {
    h += `<p class="hint">Chưa có tin chi tiết trong nhóm này.</p>`;
  }
  h += `</div></article>`;
  return h;
}

function buildDigestThesisHtml(data) {
  const mt = data.mainThesis || {};
  const sectors = ensureDigestSectors(data);
  const vn = String(data.digestVietnamHighlights || "").trim();
  const intl = String(data.digestInternationalHighlights || "").trim();
  const gaps = String(data.digestGapsAndLimits || "").trim();
  const notable = Array.isArray(data.digestNotableArticles)
    ? data.digestNotableArticles.slice(0, 9)
    : [];
  const imageByUrl = buildArticleImageLookup(data);
  const execBullets = getDigestBullets(data, "digestExecutiveBullets", mt.thesis || "");
  const intlBullets = getDigestBullets(data, "digestInternationalBullets", intl);
  const vnBullets = getDigestBullets(data, "digestVietnamBullets", vn);
  const overviewBullets = mergeOverviewBullets(execBullets, intlBullets, vnBullets);
  const articles = Array.isArray(data.articleLinkIndex) ? data.articleLinkIndex : [];
  const reportTitle =
    String(data.digestReportTitle || "").trim() ||
    "Tổng hợp tin tức toàn cầu và Việt Nam (48 giờ)";

  let thesisHtml = `<article id="digest-report" class="digest-report">`;
  thesisHtml += `<header class="digest-report-head"><h2>${escapeHtml(reportTitle)}</h2></header>`;
  thesisHtml += `<div class="digest-main-panel">`;
  if (overviewBullets.length) {
    thesisHtml += `<section class="overview-part" id="digest-main--overview">`;
    thesisHtml += `<h3 class="sectors-section-title">Tổng quan</h3>`;
    thesisHtml += buildProseBulletsHtml(overviewBullets);
    thesisHtml += `</section>`;
  }
  thesisHtml += `<section class="digest-main-sectors overview-part" id="digest-main--sectors">`;
  thesisHtml += `<h3 class="sectors-section-title">Chi tiết theo lĩnh vực</h3>`;
  if (!sectors.length) {
    thesisHtml += `<p class="error-card">Chưa có lĩnh vực trong digest.</p>`;
  } else {
    for (let i = 0; i < sectors.length; i++) {
      thesisHtml += buildSectorBlockHtml(sectors[i], i);
    }
  }
  thesisHtml += `</section>`;
  if (notable.length || articles.length) {
    thesisHtml += `<section class="overview-part digest-report-extra" id="digest-main--notable">`;
    thesisHtml += `<h3 class="sectors-section-title">Tin đáng chú ý</h3>`;
    thesisHtml += buildNotableCardsHtml(notable, imageByUrl);
    if (articles.length) {
      thesisHtml += `<details class="article-archive-wrap digest-notable-all">`;
      thesisHtml += `<summary>Bấm vào xem chi tiết · ${articles.length} bài</summary>`;
      thesisHtml += `<div class="article-archive-scroll">`;
      thesisHtml += buildLinkRowsHtml(
        articles.map((a) => ({
          url: a.url,
          title: a.title,
          source: [a.source, formatDateVi(a.publishedAt)].filter(Boolean).join(" · "),
          host: a.host || getHostName(a.url || ""),
        })),
      );
      thesisHtml += `</div></details>`;
    }
    thesisHtml += `</section>`;
  }
  if (gaps) {
    thesisHtml += `<section class="overview-part digest-report-extra" id="digest-main--gaps">`;
    thesisHtml += `<h3 class="sectors-section-title">Ghi chú</h3><p class="hint">${escapeHtml(gaps)}</p></section>`;
  }
  thesisHtml += `</div></article>`;
  return thesisHtml;
}

function applyDigestHero(html) {
  if (/<body\s+class="/i.test(html)) {
    html = html.replace(/<body\s+class="([^"]*)"/i, (m, cls) => {
      const next = cls.includes("digest-mode") ? cls : `${cls} digest-mode`.trim();
      return `<body class="${next}"`;
    });
  } else {
    html = html.replace(/<body>/i, '<body class="digest-mode">');
  }
  html = html.replace(/(<p class="hero-sub" id="heroSubtitle">)[^<]*/, "$1");
  html = html.replace(
    /(<p class="hero-desc" id="heroDescription">\s*)[\s\S]*?(\s*<\/p>)/,
    "$1$2",
  );
  return html;
}

function replaceEmptyDiv(html, id, className, inner) {
  const pattern = `<div\\s+id="${id}"\\s+class="${className}"\\s*>\\s*</div>`;
  if (!new RegExp(pattern, "i").test(html)) {
    console.error(`Placeholder not found for #${id}`);
    process.exit(1);
  }
  return html.replace(
    new RegExp(pattern, "gi"),
    `<div id="${id}" class="${className}">${inner}</div>`,
  );
}

function main() {
  const pagePath = path.resolve(process.argv[2] || "");
  const jsonPath = path.resolve(process.argv[3] || "");
  if (!pagePath || !jsonPath || !fs.existsSync(pagePath) || !fs.existsSync(jsonPath)) {
    console.error("Usage: node scripts/embed_public_brief_into_html.mjs <page.html> <content.json>");
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
  if (data.briefMode !== "multisector-digest") {
    console.error("content.json must have briefMode=multisector-digest");
    process.exit(1);
  }

  const thesisHtml = buildDigestThesisHtml(data);
  let html = fs.readFileSync(pagePath, "utf8");
  html = applyDigestHero(html);
  html = replaceEmptyDiv(html, "sectionThesis", "brief-block", thesisHtml);

  const gridPattern = `<div\\s+id="sourceGrid"\\s+class="source-grid"\\s*>\\s*</div>`;
  if (!new RegExp(gridPattern, "i").test(html)) {
    console.error("Placeholder not found for #sourceGrid");
    process.exit(1);
  }
  html = html.replace(
    new RegExp(gridPattern, "gi"),
    `<div id="sourceGrid" class="source-grid" data-embedded-articles="1"></div>`,
  );

  const st = data.generatedAt ? formatDateVi(data.generatedAt) : "";
  const syncHtml = st
    ? `<p id="syncNote" class="sync-note">Tin tức được tổng hợp lúc ${escapeHtml(st)}.</p>`
    : `<p id="syncNote" class="sync-note"></p>`;
  html = html.replace(/<p id="syncNote" class="sync-note"><\/p>/, syncHtml);
  html = html.replace('<section id="brief" class="alt">', '<section id="brief" class="alt" data-embedded-brief="1">');
  html = html.replace(
    /<div class="nav-links" id="navLinks">\s*<\/div>/i,
    '<div class="nav-links" id="navLinks"><a class="nav-hub nav-hub--active" href="#brief">Tin tức tổng hợp 24h</a></div>',
  );

  fs.writeFileSync(pagePath, html, "utf8");
  console.log("Embedded digest brief into", pagePath);
}

main();
