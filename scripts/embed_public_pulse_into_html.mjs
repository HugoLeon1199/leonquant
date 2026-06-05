/**
 * Nhúng tin LIVE (market_pulse.json) vào HTML tĩnh — GPT/crawler đọc được không cần fetch JS.
 *
 * Usage: node scripts/embed_public_pulse_into_html.mjs <page.html> <market_pulse.json>
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function normalizeExternalUrl(url) {
  let u = String(url || "").trim();
  if (!u) return "";
  if (/^https?:\/\//i.test(u)) return u;
  if (u.startsWith("//")) return "https:" + u;
  return "https://" + u.replace(/^\/+/, "");
}

function formatDateVi(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return String(iso);
  return date.toLocaleString("vi-VN", {
    timeZone: "Asia/Ho_Chi_Minh",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function pulseSourceLabel(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function pulseUrlDedupeKey(url) {
  const clean = normalizeExternalUrl(url);
  try {
    const p = new URL(clean);
    const host = p.hostname.replace(/^www\./i, "").toLowerCase();
    const pathPart = p.pathname.replace(/\/$/, "") || "/";
    return `${host}|${pathPart}`;
  } catch {
    return clean;
  }
}

function dedupePulseSources(sources) {
  const seen = new Set();
  const out = [];
  for (const s of sources || []) {
    const url = normalizeExternalUrl(String(s?.url || s || "").trim());
    if (!url.startsWith("http")) continue;
    const key = pulseUrlDedupeKey(url);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({
      url,
      name: String(s?.name || "").trim() || pulseSourceLabel(url),
      publishedAt: String(s?.publishedAt || s?.published_at || "").trim(),
    });
  }
  return out;
}

function normalizePulseSources(raw) {
  if (!Array.isArray(raw)) return [];
  const out = [];
  for (const item of raw) {
    if (!item) continue;
    if (typeof item === "string") {
      const u = normalizeExternalUrl(item);
      if (u) out.push({ url: u, name: pulseSourceLabel(u) });
      continue;
    }
    const u = normalizeExternalUrl(item.url);
    if (u) {
      const name = String(item.name || "").trim() || pulseSourceLabel(u);
      out.push({ url: u, name });
    }
  }
  return dedupePulseSources(out);
}

function buildPulseMetaRowHtml(ev) {
  const sc = Number(ev.source_count) || 0;
  const na = Number(ev.num_articles) || 0;
  const tone = String(ev.sentiment_label || "").trim();
  let h = `<div class="pulse-event-meta-row">`;
  if (ev.sector) {
    h += `<span class="pulse-radar-badge pulse-radar-badge--sector">${escapeHtml(ev.sector)}</span>`;
  }
  if (na > 0) {
    h += `<span class="pulse-radar-badge pulse-radar-badge--count">${escapeHtml(String(na))} bài</span>`;
  }
  if (sc > 0) {
    const srcClass =
      sc >= 3
        ? " pulse-radar-badge--sources-hot"
        : sc <= 1
          ? " pulse-radar-badge--sources-solo"
          : "";
    h += `<span class="pulse-radar-badge pulse-radar-badge--sources${srcClass}">${escapeHtml(String(sc))} nguồn</span>`;
  }
  if (tone) {
    h += `<span class="pulse-radar-badge pulse-radar-badge--tone">${escapeHtml(tone)}</span>`;
  }
  h += `</div>`;
  return h;
}

function buildPulseSourceLinks(sources) {
  const list = normalizePulseSources(sources);
  if (!list.length) return "";
  const rows = list
    .slice(0, 8)
    .map((src) => {
      const label = escapeHtml(src.name || pulseSourceLabel(src.url));
      return `<li><a href="${escapeHtml(src.url)}" target="_blank" rel="noopener noreferrer">${label}</a></li>`;
    })
    .join("");
  return `<div class="pulse-event-sources-block">
        <p class="pulse-event-sources-head">Nguồn</p>
        <ul class="pulse-event-source-links">${rows}</ul>
      </div>`;
}

function buildPulseHtml(data) {
  const events = Array.isArray(data.events) ? data.events : [];
  if (!events.length) {
    return `<div class="pulse-panel"><p class="hint">Chưa có tin LIVE.</p></div>`;
  }
  const updated = formatDateVi(data.generated_at_utc);
  let h = `<article class="digest-report" id="pulse-crawler-report">`;
  h += `<header class="digest-report-head"><h2>NÓNG TOÀN CẦU <span class="pulse-title-live">🔴 LIVE</span></h2>`;
  if (updated) h += `<p class="sync-note">Cập nhật ${escapeHtml(updated)} (giờ Việt Nam).</p>`;
  h += `</header><div class="pulse-panel"><ol class="pulse-event-list">`;
  for (const ev of events) {
    const sc = Number(ev.source_count) || 0;
    const cardClass =
      sc >= 3 ? " pulse-event--multi-source" : sc <= 1 ? " pulse-event--solo-source" : "";
    h += `<li class="pulse-event${cardClass}">`;
    h += buildPulseMetaRowHtml(ev);
    h += `<h3 class="pulse-event-title">${escapeHtml(ev.title)}</h3>`;
    if (ev.summary) h += `<p class="pulse-event-hint">${escapeHtml(ev.summary)}</p>`;
    if (ev.importance_reason) {
      h += `<p class="pulse-event-importance">${escapeHtml(ev.importance_reason)}</p>`;
    }
    const na = ev.num_articles ?? "—";
    const scText = ev.source_count ?? "—";
    const tone = ev.sentiment_label || "";
    h += `<p class="pulse-event-coverage">Độ phủ: <strong>${escapeHtml(na)}</strong> bài · <strong>${escapeHtml(scText)}</strong> nguồn`;
    if (tone) h += ` · ${escapeHtml(tone)}`;
    h += `</p>`;
    h += buildPulseSourceLinks(ev.sources);
    h += `</li>`;
  }
  h += `</ol></div></article>`;
  return h;
}

function replacePulseBlock(html, inner) {
  const emptyPattern =
    /(<section id="pulse"[^>]*>\s*<div class="container">\s*)<div id="sectionPulse" class="brief-block"\s*>\s*<\/div>/i;
  if (emptyPattern.test(html)) {
    return html.replace(
      emptyPattern,
      `$1<div id="sectionPulse" class="brief-block">${inner}</div>`,
    );
  }
  const filled = new RegExp(
    '(<section id="pulse"[^>]*>\\s*<div class="container">\\s*)' +
      '<div id="sectionPulse" class="brief-block"[^>]*>[\\s\\S]*?' +
      '(?=</div>\\s*</div>\\s*</section>)',
    "i",
  );
  if (!filled.test(html)) {
    console.error("Block not found for #sectionPulse inside #pulse");
    process.exit(1);
  }
  return html.replace(
    filled,
    `$1<div id="sectionPulse" class="brief-block">${inner}</div>\n        `,
  );
}

function main() {
  const pagePath = path.resolve(process.argv[2] || "");
  const jsonPath = path.resolve(process.argv[3] || "");
  if (!pagePath || !jsonPath || !fs.existsSync(pagePath) || !fs.existsSync(jsonPath)) {
    console.error("Usage: node scripts/embed_public_pulse_into_html.mjs <page.html> <market_pulse.json>");
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
  const inner = buildPulseHtml(data);
  let html = fs.readFileSync(pagePath, "utf8");
  html = replacePulseBlock(html, inner);
  html = html.replace(/<div id="sectionPulse"([^>]*)>/i, (m, attrs) => {
    if (/data-embedded-pulse/i.test(attrs)) return m;
    return `<div id="sectionPulse"${attrs} data-embedded-pulse="1">`;
  });
  html = html.replace(
    /<section id="pulse"([^>]*)>/i,
    '<section id="pulse"$1 data-embedded-pulse="1">',
  );
  fs.writeFileSync(pagePath, html, "utf8");
  console.log("Embedded LIVE pulse into", pagePath);
}

main();
