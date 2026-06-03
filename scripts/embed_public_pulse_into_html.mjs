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
    const sources = (Array.isArray(ev.sources) ? ev.sources : [])
      .map((u) => normalizeExternalUrl(u))
      .filter(Boolean)
      .slice(0, 8);
    if (sources.length) {
      h += `<ul class="link-rows pulse-embed-sources">`;
      for (const u of sources) {
        const label = escapeHtml(pulseSourceLabel(u));
        h += `<li><a href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">${label}</a></li>`;
      }
      h += `</ul>`;
    }
    h += `</li>`;
  }
  h += `</ol></div></article>`;
  return h;
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
    console.error("Usage: node scripts/embed_public_pulse_into_html.mjs <page.html> <market_pulse.json>");
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
  const inner = buildPulseHtml(data);
  let html = fs.readFileSync(pagePath, "utf8");
  html = replaceEmptyDiv(html, "sectionPulse", "brief-block", inner);
  html = html.replace(
    /<section id="pulse"([^>]*)>/i,
    '<section id="pulse"$1 data-embedded-pulse="1">',
  );
  fs.writeFileSync(pagePath, html, "utf8");
  console.log("Embedded LIVE pulse into", pagePath);
}

main();
