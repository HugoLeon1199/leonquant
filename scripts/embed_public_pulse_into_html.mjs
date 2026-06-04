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
  return out;
}

function buildPulseSourcesTicker(sources) {
  let list = normalizePulseSources(sources);
  if (!list.length) return "";
  const base = list.slice();
  while (list.length < 6) list = list.concat(base);
  const rows = list
    .map((src) => {
      const label = escapeHtml(src.name || pulseSourceLabel(src.url));
      return `<li><a href="${escapeHtml(src.url)}" target="_blank" rel="noopener noreferrer">${label}</a></li>`;
    })
    .join("");
  return `<div class="pulse-event-sources-block">
        <p class="pulse-event-sources-head">Nguồn</p>
        <div class="pulse-sources-ticker">
          <div class="pulse-sources-ticker-viewport">
            <div class="pulse-sources-ticker-scroll">
              <ul class="pulse-sources-ticker-list">${rows}</ul>
              <ul class="pulse-sources-ticker-list" aria-hidden="true">${rows}</ul>
            </div>
          </div>
        </div>
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
    h += `<li class="pulse-event">`;
    if (ev.sector) h += `<p class="pulse-event-sector">${escapeHtml(ev.sector)}</p>`;
    h += `<h3 class="pulse-event-title">${escapeHtml(ev.title)}</h3>`;
    if (ev.summary) h += `<p class="pulse-event-hint">${escapeHtml(ev.summary)}</p>`;
    if (ev.importance_reason) {
      h += `<p class="pulse-event-importance">${escapeHtml(ev.importance_reason)}</p>`;
    }
    const na = ev.num_articles ?? "—";
    const sc = ev.source_count ?? "—";
    const tone = ev.sentiment_label || "";
    h += `<p class="pulse-event-coverage">Độ phủ: <strong>${escapeHtml(na)}</strong> bài · <strong>${escapeHtml(sc)}</strong> nguồn`;
    if (tone) h += ` · ${escapeHtml(tone)}`;
    h += `</p>`;
    h += buildPulseSourcesTicker(ev.sources);
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
  // Only replace #sectionPulse inside #pulse — do not match across #invest (old nextId=sectionInvest boundary swallowed <section id="invest">).
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
