/**
 * Nhúng khối Việt Nam (invest_vn_brief.json) vào tab đầu tư — không đụng brief/pulse.
 *
 * Usage: node scripts/embed_public_invest_vn_into_html.mjs <page.html> <invest_vn_brief.json>
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

function buildVnLinksHtml(links) {
  if (!Array.isArray(links) || !links.length) return "";
  let h = `<ul class="invest-vn-link-rows">`;
  for (const lk of links) {
    const u = normalizeExternalUrl(lk.url);
    if (!u) continue;
    const label = escapeHtml(lk.title || lk.source || u);
    h += `<li><a href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">${label}</a>`;
    if (lk.source) h += `<span class="link-meta"> — ${escapeHtml(lk.source)}</span>`;
    h += `</li>`;
  }
  h += `</ul>`;
  return h;
}

function buildInvestVnHtml(data) {
  const themes = Array.isArray(data.themes_48h) ? data.themes_48h : [];
  const watch = Array.isArray(data.now_watch) ? data.now_watch : [];
  const updated = formatDateVi(data.source_digest_at || data.generated_at_utc);
  let h = `<section class="invest-desk-section invest-desk-section--vn" data-embedded-invest-vn="1">`;
  h += `<header class="invest-desk-head">`;
  h += `<h3 class="invest-desk-title">Việt Nam trong nước</h3>`;
  h += `<p class="invest-desk-sub">Phân tích từ tin 48 giờ · chi tiết &amp; góc đầu tư</p>`;
  if (updated) h += `<p class="sync-note">Dữ liệu digest: ${escapeHtml(updated)}</p>`;
  h += `</header>`;
  if (data.lead) {
    h += `<p class="invest-vn-lead">${escapeHtml(data.lead)}</p>`;
  }
  if (themes.length) {
    const themesLabel =
      String(data.themes_section_label || "").trim() ||
      "Ba điểm đáng chú ý trong 48 giờ qua";
    h += `<h4 class="sectors-section-title">${escapeHtml(themesLabel)}</h4>`;
    h += `<ol class="invest-vn-theme-list">`;
    for (const th of themes) {
      h += `<li class="invest-vn-theme">`;
      h += `<p class="invest-vn-theme-rank">${String(th.rank || "").padStart(2, "0")}</p>`;
      h += `<div class="invest-vn-theme-body">`;
      h += `<h5 class="invest-vn-theme-title">${escapeHtml(th.title)}</h5>`;
      if (th.why_hot) h += `<p class="invest-vn-why">${escapeHtml(th.why_hot)}</p>`;
      if (Array.isArray(th.developments) && th.developments.length) {
        h += `<ul class="sector-points prose-bullets">`;
        for (const d of th.developments) {
          h += `<li>${escapeHtml(d)}</li>`;
        }
        h += `</ul>`;
      }
      if (th.investor_lens) {
        h += `<p class="invest-vn-lens"><strong>Góc đầu tư:</strong> ${escapeHtml(th.investor_lens)}</p>`;
      }
      h += buildVnLinksHtml(th.links);
      h += `</div></li>`;
    }
    h += `</ol>`;
  }
  if (watch.length) {
    h += `<h4 class="sectors-section-title">Đang theo dõi / hiện tại</h4>`;
    h += `<ul class="invest-vn-watch-list">`;
    for (const nw of watch) {
      h += `<li class="invest-vn-watch">`;
      h += `<h5 class="invest-vn-watch-title">${escapeHtml(nw.title)}</h5>`;
      if (nw.status) {
        h += `<p class="invest-vn-watch-status"><span class="invest-vn-status-pill">${escapeHtml(nw.status)}</span></p>`;
      }
      if (nw.issue) {
        h += `<p class="invest-vn-watch-body"><strong>Vấn đề:</strong> ${escapeHtml(nw.issue)}</p>`;
      }
      if (nw.affected_groups) {
        h += `<p class="invest-vn-watch-body"><strong>Nhóm ảnh hưởng:</strong> ${escapeHtml(nw.affected_groups)}</p>`;
      }
      if (nw.watch_variables) {
        h += `<p class="invest-vn-watch-body"><strong>Biến số cần theo dõi:</strong> ${escapeHtml(nw.watch_variables)}</p>`;
      }
      h += buildVnLinksHtml(nw.links);
      h += `</li>`;
    }
    h += `</ul>`;
  }
  if (!themes.length && !watch.length) {
    h += `<p class="hint">Chưa có phân tích VN. Chạy digest ngày hoặc kiểm tra invest_vn_brief.json.</p>`;
  }
  if (data.gaps) {
    h += `<p class="hint invest-vn-gaps">${escapeHtml(data.gaps)}</p>`;
  }
  h += `</section>`;
  return h;
}

function main() {
  const pagePath = path.resolve(process.argv[2] || "");
  const jsonPath = path.resolve(process.argv[3] || "");
  if (!pagePath || !jsonPath || !fs.existsSync(pagePath) || !fs.existsSync(jsonPath)) {
    console.error("Usage: node scripts/embed_public_invest_vn_into_html.mjs <page.html> <invest_vn_brief.json>");
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
  const inner = buildInvestVnHtml(data);
  let html = fs.readFileSync(pagePath, "utf8");
  const empty = /<div\s+id="sectionInvestVn"\s+class="invest-desk-block"\s*>\s*<\/div>/i;
  const filled =
    /<div\s+id="sectionInvestVn"\s+class="invest-desk-block">[\s\S]*?<\/div>(?=\s*\n\s*<\/article>)/i;
  const replacement = `<div id="sectionInvestVn" class="invest-desk-block">${inner}</div>`;
  if (empty.test(html)) {
    html = html.replace(empty, replacement);
  } else if (filled.test(html)) {
    html = html.replace(filled, replacement);
  } else {
    console.error("Placeholder #sectionInvestVn not found");
    process.exit(1);
  }
  fs.writeFileSync(pagePath, html, "utf8");
  console.log("Embedded invest VN brief into", pagePath);
}

main();
