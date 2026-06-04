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

function replaceBriefBlock(html, id, className, inner, nextId = "") {
  const emptyPattern = `<div\\s+id="${id}"\\s+class="${className}"\\s*>\\s*</div>`;
  if (new RegExp(emptyPattern, "i").test(html)) {
    return html.replace(
      new RegExp(emptyPattern, "gi"),
      `<div id="${id}" class="${className}">${inner}</div>`,
    );
  }
  const boundary = nextId
    ? `(?=\\s*<div\\s+id="${nextId}")`
    : `(?=\\s*<div\\s+id="section)`;
  const filled = new RegExp(
    `<div\\s+id="${id}"\\s+class="${className}"[^>]*>[\\s\\S]*?${boundary}`,
    "i",
  );
  if (!filled.test(html)) {
    console.error(`Block not found for #${id}`);
    process.exit(1);
  }
  return html.replace(
    filled,
    `<div id="${id}" class="${className}">${inner}</div>\n        `,
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
  html = replaceBriefBlock(html, "sectionPulse", "brief-block", inner, "sectionInvest");
  html = html.replace(
    /<section id="pulse"([^>]*)>/i,
    '<section id="pulse"$1 data-embedded-pulse="1">',
  );
  fs.writeFileSync(pagePath, html, "utf8");
  console.log("Embedded LIVE pulse into", pagePath);
}

main();
