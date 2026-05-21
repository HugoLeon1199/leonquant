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

function ensureDigestSectors(data) {
  if (Array.isArray(data.digestSectors) && data.digestSectors.length) {
    return data.digestSectors.filter((s) => s && typeof s === "object");
  }
  const drivers = Array.isArray(data.globalMacroDrivers) ? data.globalMacroDrivers : [];
  return drivers.map((d) => ({
    name: d.title || "Lĩnh vực",
    summary: d.analysis || "",
    keyPoints: String(d.marketImpact || "")
      .split("\n")
      .map((x) => x.replace(/^•\s*/, "").trim())
      .filter(Boolean),
    links: [],
  }));
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

function buildSectorsIndexHtml(sectors) {
  let h = `<div class="sectors-index"><p class="lbl-inline">Mục lục ${sectors.length} lĩnh vực</p><ol>`;
  for (let i = 0; i < sectors.length; i++) {
    const name = String(sectors[i].name || "").trim();
    if (!name) continue;
    const id = sectorSlug(name);
    h += `<li><a href="#${id}">${i + 1}. ${escapeHtml(name)}</a></li>`;
  }
  h += `</ol></div>`;
  return h;
}

function buildSectorBlockHtml(s, index) {
  const name = String(s.name || "").trim() || "Lĩnh vực";
  const id = sectorSlug(name);
  const pts = Array.isArray(s.keyPoints) ? s.keyPoints : [];
  const hasSummary = Boolean(String(s.summary || "").trim());
  let h = `<article class="sector-block" id="${id}">`;
  h += `<header class="sector-head"><span class="sector-num">${String(index + 1).padStart(2, "0")}</span>`;
  h += `<h3>${escapeHtml(name)}</h3></header><div class="sector-body">`;
  if (hasSummary) h += `<p class="sector-summary">${escapeHtml(s.summary)}</p>`;
  if (pts.length) {
    h += `<ul class="sector-points">`;
    for (const p of pts) h += `<li>${escapeHtml(p)}</li>`;
    h += `</ul>`;
  }
  if (!hasSummary && !pts.length) {
    h += `<p class="hint">Chưa có nội dung chi tiết cho lĩnh vực này.</p>`;
  }
  h += `</div></article>`;
  return h;
}

function collectDigestNotableLinks(notable, sectors) {
  const seen = new Set();
  const out = [];
  const push = (row) => {
    if (!row || typeof row !== "object") return;
    const u = String(row.url || "").trim();
    if (!u || seen.has(u)) return;
    seen.add(u);
    out.push({
      url: u,
      title: row.title || row.host || u,
      source: row.source || "",
      host: row.host || getHostName(u),
    });
  };
  for (const a of notable) {
    push({
      url: a.url,
      title: a.title,
      source: [a.source, a.whyNotable].filter(Boolean).join(" · "),
      host: getHostName(a.url || ""),
    });
  }
  for (const s of sectors) {
    for (const L of Array.isArray(s.links) ? s.links : []) push(L);
  }
  return out;
}

function buildDigestThesisHtml(data) {
  const mt = data.mainThesis || {};
  const sectors = ensureDigestSectors(data);
  const vn = String(data.digestVietnamHighlights || "").trim();
  const intl = String(data.digestInternationalHighlights || "").trim();
  const gaps = String(data.digestGapsAndLimits || "").trim();
  const notable = Array.isArray(data.digestNotableArticles) ? data.digestNotableArticles : [];
  const execBullets = getDigestBullets(data, "digestExecutiveBullets", mt.thesis || "");
  const intlBullets = getDigestBullets(data, "digestInternationalBullets", intl);
  const vnBullets = getDigestBullets(data, "digestVietnamBullets", vn);
  const overviewBullets = mergeOverviewBullets(execBullets, intlBullets, vnBullets);
  const reportTitle =
    String(data.digestReportTitle || "").trim() ||
    "Tổng hợp tin tức toàn cầu và Việt Nam (48 giờ)";

  const mainToc = [];
  if (overviewBullets.length) mainToc.push({ id: "overview", label: "Tổng quan" });
  if (sectors.length) mainToc.push({ id: "sectors", label: "Chi tiết theo lĩnh vực" });
  for (const s of sectors) {
    const name = String(s.name || "").trim();
    if (!name) continue;
    mainToc.push({ id: sectorSlug(name), label: name, external: true });
  }
  const articles = Array.isArray(data.articleLinkIndex) ? data.articleLinkIndex : [];
  const notableLinks = collectDigestNotableLinks(notable, sectors);
  if (notableLinks.length || articles.length) {
    mainToc.push({ id: "notable", label: "Tin đáng chú ý" });
  }

  let thesisHtml = `<article id="digest-report" class="digest-report">`;
  thesisHtml += `<header class="digest-report-head"><h2>${escapeHtml(reportTitle)}</h2></header>`;
  thesisHtml += `<div class="digest-main-panel">`;
  if (mainToc.length) {
    thesisHtml += `<ul class="overview-mini-toc" aria-label="Mục lục bản tin">`;
    for (const it of mainToc) {
      const href = it.external ? `#${it.id}` : `#digest-main--${it.id}`;
      thesisHtml += `<li><a href="${href}">${escapeHtml(it.label)}</a></li>`;
    }
    thesisHtml += `</ul>`;
  }
  if (overviewBullets.length) {
    thesisHtml += `<section class="overview-part" id="digest-main--overview">`;
    thesisHtml += `<p class="sector-part-title">Tổng quan</p>`;
    thesisHtml += buildProseBulletsHtml(overviewBullets);
    thesisHtml += `</section>`;
  }
  thesisHtml += `<section class="digest-main-sectors overview-part" id="digest-main--sectors">`;
  thesisHtml += `<p class="sector-part-title">Chi tiết theo lĩnh vực</p>`;
  if (!sectors.length) {
    thesisHtml += `<p class="error-card">Chưa có lĩnh vực trong digest.</p>`;
  } else {
    thesisHtml += buildSectorsIndexHtml(sectors);
    for (let i = 0; i < sectors.length; i++) {
      thesisHtml += buildSectorBlockHtml(sectors[i], i);
    }
  }
  thesisHtml += `</section>`;
  if (notableLinks.length || articles.length) {
    thesisHtml += `<section class="overview-part digest-report-extra" id="digest-main--notable">`;
    thesisHtml += `<p class="sector-part-title">Tin đáng chú ý</p>`;
    if (notableLinks.length) {
      thesisHtml += buildLinkRowsHtml(
        notableLinks.map((a) => ({
          url: a.url,
          title: a.title,
          source: a.source,
          host: a.host || getHostName(a.url || ""),
        })),
      );
    }
    if (articles.length) {
      thesisHtml += `<details class="article-index-wrap digest-notable-all">`;
      thesisHtml += `<summary>Bấm vào xem chi tiết</summary>`;
      thesisHtml += `<div class="article-index-scroll">`;
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
    thesisHtml += `<p class="sector-part-title">Ghi chú</p><p class="hint">${escapeHtml(gaps)}</p></section>`;
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

  fs.writeFileSync(pagePath, html, "utf8");
  console.log("Embedded digest brief into", pagePath);
}

main();
