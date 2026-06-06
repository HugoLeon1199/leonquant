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

function investFieldRow(label, innerHtml) {
  const body = String(innerHtml || "").trim();
  if (!body) return "";
  return (
    `<div class="invest-field-row">` +
    `<span class="invest-field-label">${escapeHtml(label)}</span>` +
    `<div class="invest-field-body">${body}</div>` +
    `</div>`
  );
}

function investBadgeRow(items, badgeClass) {
  const list = (Array.isArray(items) ? items : [])
    .map((x) => String(x || "").trim())
    .filter(Boolean);
  if (!list.length) return "";
  const cls = badgeClass ? ` invest-badge--${badgeClass}` : "";
  return `<div class="invest-badge-row">${list
    .map((x) => `<span class="invest-badge${cls}">${escapeHtml(x)}</span>`)
    .join("")}</div>`;
}

function buildVnLinksHtml(links) {
  if (!Array.isArray(links) || !links.length) return "";
  let h = `<ul class="invest-vn-link-rows">`;
  for (const lk of links) {
    const u = normalizeExternalUrl(lk.url);
    if (!u) continue;
    const label = escapeHtml(lk.title || lk.source || u);
    h += `<li><a href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">${label}</a>`;
    const meta = [formatDateVi(lk.publishedAt || lk.published_at), lk.source]
      .filter(Boolean)
      .join(" · ");
    if (meta) h += `<span class="link-meta">${escapeHtml(meta)}</span>`;
    h += `</li>`;
  }
  h += `</ul>`;
  return h;
}

function buildInvestVnHtml(data) {
  const themes = Array.isArray(data.themes_48h) ? data.themes_48h : [];
  const watch = Array.isArray(data.now_watch) ? data.now_watch : [];
  const updated = formatDateVi(data.source_digest_at || data.generated_at_utc);
  let h = `<section id="invest-vn" class="invest-desk-section invest-desk-section--vn" data-embedded-invest-vn="1">`;
  h += `<header class="invest-desk-head">`;
  h += `<h3 class="invest-desk-title">Việt Nam &amp; thị trường trong nước</h3>`;
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
      h += investFieldRow(
        "Chủ đề",
        `<h5 class="invest-vn-theme-title">${escapeHtml(th.title)}</h5>`,
      );
      let devBody = "";
      if (th.why_hot) devBody += `<p class="invest-vn-why">${escapeHtml(th.why_hot)}</p>`;
      if (Array.isArray(th.developments) && th.developments.length) {
        devBody += `<ul class="sector-points prose-bullets">`;
        for (const d of th.developments) {
          devBody += `<li>${escapeHtml(d)}</li>`;
        }
        devBody += `</ul>`;
      }
      if (devBody) h += investFieldRow("Diễn biến chính", devBody);
      if (th.investor_lens) {
        h += investFieldRow(
          "Góc đầu tư",
          `<p class="invest-vn-lens">${escapeHtml(th.investor_lens)}</p>`,
        );
      }
      const linksHtml = buildVnLinksHtml(th.links);
      if (linksHtml) h += investFieldRow("Nguồn", linksHtml);
      h += `</div></li>`;
    }
    h += `</ol>`;
  }
  if (watch.length) {
    h += `<div id="invest-watch" class="invest-vn-watch-block">`;
    h += `<h4 class="sectors-section-title">Đang theo dõi</h4>`;
    h += `<ul class="invest-vn-watch-list">`;
    for (const nw of watch) {
      h += `<li class="invest-vn-watch">`;
      h += investFieldRow(
        "Chủ đề",
        `<h5 class="invest-vn-watch-title">${escapeHtml(nw.title)}</h5>` +
          (nw.status
            ? `<p class="invest-vn-watch-status"><span class="invest-vn-status-pill">${escapeHtml(nw.status)}</span></p>`
            : ""),
      );
      if (nw.issue) {
        h += investFieldRow(
          "Diễn biến chính",
          `<p class="invest-vn-watch-body">${escapeHtml(nw.issue)}</p>`,
        );
      }
      const watchBits = [];
      if (nw.affected_groups) watchBits.push(String(nw.affected_groups).trim());
      if (nw.watch_variables) watchBits.push(String(nw.watch_variables).trim());
      if (watchBits.length) {
        h += investFieldRow(
          "Nhóm ảnh hưởng / biến số theo dõi",
          investBadgeRow(watchBits, "watch"),
        );
      }
      const linksHtml = buildVnLinksHtml(nw.links);
      if (linksHtml) h += investFieldRow("Nguồn", linksHtml);
      h += `</li>`;
    }
        h += `</ul></div>`;
      } else {
        h += `<div id="invest-watch" class="invest-vn-watch-block" hidden aria-hidden="true"></div>`;
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
    /<div\s+id="sectionInvestVn"\s+class="invest-desk-block">[\s\S]*?<\/div>(?=\s*\n\s*<\/div>\s*\n\s*<\/article>)/i;
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
