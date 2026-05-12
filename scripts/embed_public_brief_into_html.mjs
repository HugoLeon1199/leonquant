/**
 * Nhúng brief + lưới tin từ content.json vào HTML tĩnh (GitHub Pages).
 * Đảm bảo trang hiển thị đầy đủ khi JS / fetch lỗi (Cloudflare, CSP, v.v.).
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

function renderTable(headers, rows) {
  let h = `<div class="data-table-wrap"><table class="data"><thead><tr>`;
  for (const x of headers) h += `<th>${escapeHtml(x)}</th>`;
  h += `</tr></thead><tbody>`;
  for (const row of rows) {
    h += `<tr>`;
    for (const cell of row) h += `<td>${cell}</td>`;
    h += `</tr>`;
  }
  h += `</tbody></table></div>`;
  return h;
}

function buildBriefParts(data) {
  const mt = data.mainThesis || {};
  const drivers = (Array.isArray(data.globalMacroDrivers) ? data.globalMacroDrivers : []).filter(
    (r) => r && typeof r === "object",
  );
  const qa = (Array.isArray(data.quickActions) ? data.quickActions : []).filter((r) => r && typeof r === "object");
  const ag = (Array.isArray(data.allocationGuide) ? data.allocationGuide : []).filter((r) => r && typeof r === "object");
  const sp = (Array.isArray(data.sectorPriority) ? data.sectorPriority : []).filter((r) => r && typeof r === "object");
  const ir = (Array.isArray(data.increaseRiskSignals) ? data.increaseRiskSignals : []).filter(
    (r) => r && typeof r === "object",
  );
  const rr = (Array.isArray(data.reduceRiskSignals) ? data.reduceRiskSignals : []).filter(
    (r) => r && typeof r === "object",
  );
  const vt = data.vietnamTransmission || {};
  const chains = Array.isArray(vt.chains) ? vt.chains : [];
  const scen = data.scenarioPlan || {};

  let thesisHtml = "";
  thesisHtml += `<div class="section-head"><p class="eyebrow">Luận điểm</p><h2>Luận điểm chính hôm nay</h2></div>`;
  thesisHtml += `<div class="thesis-block">`;
  thesisHtml += `<p class="lbl">Trạng thái / nhịp thị trường</p><p>${escapeHtml(mt.regime || ND)}</p>`;
  thesisHtml += `<p class="lbl">Luận điểm</p><p>${escapeHtml(mt.thesis || ND)}</p>`;
  thesisHtml += `<p class="lbl">Kết luận hành động</p><p>${escapeHtml(mt.actionConclusion || ND)}</p>`;
  thesisHtml += `</div>`;

  let macroHtml = "";
  macroHtml += `<div class="section-head"><p class="eyebrow">Vĩ mô</p><h2>Vĩ mô thế giới đang tác động gì?</h2></div>`;
  if (!drivers.length) {
    macroHtml += `<p class="error-card">Chưa có nội dung vĩ mô.</p>`;
  } else {
    macroHtml += `<div class="cards">`;
    for (let i = 0; i < drivers.length; i++) {
      const d = drivers[i];
      macroHtml += `<article class="card"><h3>${i + 1}. ${escapeHtml(d.title || ND)}</h3>`;
      macroHtml += `<p class="sub">Phân tích</p><p class="body">${escapeHtml(d.analysis || ND)}</p>`;
      macroHtml += `<p class="sub">Tác động tới Việt Nam</p><p class="body">${escapeHtml(d.vietnamImpact || ND)}</p></article>`;
    }
    macroHtml += `</div>`;
  }

  let transmissionHtml = "";
  transmissionHtml += `<div class="section-head"><p class="eyebrow">Truyền dẫn</p><h2>Chuỗi tác động đến Việt Nam</h2></div>`;
  transmissionHtml += `<div class="thesis-block"><p>${escapeHtml(vt.summary || ND)}</p>`;
  if (chains.length) {
    transmissionHtml += `<ul class="chain-list">`;
    for (const c of chains) transmissionHtml += `<li>${escapeHtml(c)}</li>`;
    transmissionHtml += `</ul>`;
  }
  transmissionHtml += `</div>`;

  let actionsHtml = "";
  actionsHtml += `<div class="section-head"><p class="eyebrow">Thực thi</p><h2>Hành động nhanh hôm nay</h2></div>`;
  actionsHtml += renderTable(
    ["Trạng thái nhà đầu tư", "Hành động phù hợp"],
    qa.map((r) => [escapeHtml(r.investorState || ND), escapeHtml(r.action || ND)]),
  );

  let allocationHtml = "";
  allocationHtml += `<div class="section-head"><p class="eyebrow">Danh mục</p><h2>Phân bổ vốn tham khảo</h2></div>`;
  allocationHtml += renderTable(
    ["Hồ sơ rủi ro", "Cổ phiếu", "Tiền mặt", "Margin"],
    ag.map((r) => [
      escapeHtml(r.profile || ND),
      escapeHtml(r.stocks || ND),
      escapeHtml(r.cash || ND),
      escapeHtml(r.margin || ND),
    ]),
  );

  let sectorsHtml = "";
  sectorsHtml += `<div class="section-head"><p class="eyebrow">Ngành</p><h2>Ưu tiên nhóm ngành</h2></div>`;
  sectorsHtml += renderTable(
    ["Nhóm ngành", "Quan điểm", "Hành động"],
    sp.map((r) => [escapeHtml(r.sector || ND), escapeHtml(r.view || ND), escapeHtml(r.action || ND)]),
  );

  let riskOnHtml = "";
  riskOnHtml += `<div class="section-head"><p class="eyebrow">Tăng tỷ trọng</p><h2>Tín hiệu để tăng tỷ trọng</h2></div>`;
  riskOnHtml += renderTable(
    ["Tín hiệu", "Ý nghĩa"],
    ir.map((r) => [escapeHtml(r.signal || ND), escapeHtml(r.meaning || ND)]),
  );

  let riskOffHtml = "";
  riskOffHtml += `<div class="section-head"><p class="eyebrow">Rủi ro</p><h2>Tín hiệu cần giảm rủi ro</h2></div>`;
  riskOffHtml += renderTable(
    ["Tín hiệu cảnh báo", "Hành động"],
    rr.map((r) => [escapeHtml(r.signal || ND), escapeHtml(r.action || ND)]),
  );

  let scenariosHtml = "";
  scenariosHtml += `<div class="section-head"><p class="eyebrow">Kịch bản</p><h2>Kế hoạch theo 3 kịch bản</h2></div>`;
  const b = scen.baseCase || {};
  const u = scen.bullCase || {};
  const e = scen.bearCase || {};
  scenariosHtml += `<div class="scenario-grid">`;
  scenariosHtml += `<article class="sc"><h3>${escapeHtml(b.title || "Kịch bản cơ sở")}</h3><p>${escapeHtml(b.description || ND)}</p><p class="sub" style="margin-top:12px">Hành động</p><p>${escapeHtml(b.action || ND)}</p></article>`;
  scenariosHtml += `<article class="sc bull"><h3>${escapeHtml(u.title || "Kịch bản tích cực")}</h3><p>${escapeHtml(u.description || ND)}</p><p class="sub" style="margin-top:12px">Hành động</p><p>${escapeHtml(u.action || ND)}</p></article>`;
  scenariosHtml += `<article class="sc bear"><h3>${escapeHtml(e.title || "Kịch bản tiêu cực")}</h3><p>${escapeHtml(e.description || ND)}</p><p class="sub" style="margin-top:12px">Hành động</p><p>${escapeHtml(e.action || ND)}</p></article>`;
  scenariosHtml += `</div>`;

  let takeawayHtml = "";
  takeawayHtml += `<div class="section-head"><p class="eyebrow">Đóng phiên</p><h2>Kết luận hôm nay</h2></div>`;
  takeawayHtml += `<div class="takeaway"><p>${escapeHtml(data.finalTakeaway || ND)}</p></div>`;

  return {
    thesis: thesisHtml,
    macro: macroHtml,
    transmission: transmissionHtml,
    actions: actionsHtml,
    allocation: allocationHtml,
    sectors: sectorsHtml,
    riskOn: riskOnHtml,
    riskOff: riskOffHtml,
    scenarios: scenariosHtml,
    takeaway: takeawayHtml,
  };
}

function buildArticleCardsHtml(articles) {
  if (!Array.isArray(articles)) return "";
  let html = "";
  for (const item of articles) {
    if (!item || !item.url) continue;
    const thumbBlock = item.image_url
      ? `<div><img class="source-image" src="${escapeHtml(item.image_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" /></div>`
      : `<div><div class="fallback-image">LQ</div></div>`;
    const meta = [item.category, item.source, formatDateVi(item.published_at)].filter(Boolean).join(" · ");
    html += `<article class="source-card"><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">`;
    html += thumbBlock;
    html += `<div class="source-body">`;
    html += `<div class="source-meta">${escapeHtml(meta)}</div>`;
    html += `<h3>${escapeHtml(item.title || "Tin")}</h3>`;
    html += `<p>${escapeHtml(item.summary || "")}</p>`;
    html += `<span class="read-pill">Đọc bài gốc → ${escapeHtml(getHostName(item.url))}</span>`;
    html += `</div></a></article>`;
  }
  return html;
}

function updateHero(html, data) {
  const pub = data.publicationIntro || {};
  const headline = String(pub.headline || "").trim();
  const desc = String(pub.description || "").trim();
  if (headline) {
    html = html.replace(
      /(<p class="hero-sub" id="heroSubtitle">)[^<]*/,
      `$1${escapeHtml(headline)}`,
    );
  }
  if (desc) {
    html = html.replace(
      /(<p class="hero-desc" id="heroDescription">\s*)[\s\S]*?(\s*<\/p>)/,
      `$1${escapeHtml(desc)}$2`,
    );
  }
  return html;
}

function syncNoteHtml(generatedAt) {
  const st = generatedAt ? formatDateVi(generatedAt) : "";
  if (!st) return `<p id="syncNote" class="sync-note"></p>`;
  return `<p id="syncNote" class="sync-note">Bản brief · ${escapeHtml(st)} (bản đóng gói trên trang). Khi tải được content.json, trang sẽ cập nhật tự động.</p>`;
}

function main() {
  const pagePath = path.resolve(process.argv[2] || "");
  const jsonPath = path.resolve(process.argv[3] || "");
  if (!pagePath || !jsonPath || !fs.existsSync(pagePath) || !fs.existsSync(jsonPath)) {
    console.error("Usage: node scripts/embed_public_brief_into_html.mjs <page.html> <content.json>");
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
  const parts = buildBriefParts(data);
  const ids = [
    "sectionThesis",
    "sectionMacro",
    "sectionTransmission",
    "sectionActions",
    "sectionAllocation",
    "sectionSectors",
    "sectionRiskOn",
    "sectionRiskOff",
    "sectionScenarios",
    "sectionTakeaway",
  ];
  const keys = [
    "thesis",
    "macro",
    "transmission",
    "actions",
    "allocation",
    "sectors",
    "riskOn",
    "riskOff",
    "scenarios",
    "takeaway",
  ];

  let html = fs.readFileSync(pagePath, "utf8");
  html = updateHero(html, data);

  for (let i = 0; i < ids.length; i++) {
    const id = ids[i];
    const inner = parts[keys[i]] || "";
    const re = new RegExp(`<div id="${id}" class="brief-block"></div>`, "g");
    html = html.replace(re, `<div id="${id}" class="brief-block">${inner}</div>`);
  }

  const articles = Array.isArray(data.allArticles) ? data.allArticles : [];
  const gridInner = buildArticleCardsHtml(articles);
  html = html.replace(
    `<div id="sourceGrid" class="source-grid"></div>`,
    `<div id="sourceGrid" class="source-grid" data-embedded-articles="1">${gridInner}</div>`,
  );
  html = html.replace(
    `<h2 id="sourceGridTitle">Tin nền tham khảo</h2>`,
    `<h2 id="sourceGridTitle">Tin nền tham khảo (${articles.length})</h2>`,
  );

  html = html.replace(
    /<p id="syncNote" class="sync-note"><\/p>/,
    syncNoteHtml(data.generatedAt),
  );

  html = html.replace('<section id="brief" class="alt">', '<section id="brief" class="alt" data-embedded-brief="1">');

  fs.writeFileSync(pagePath, html, "utf8");
  console.log("Embedded brief + articles into", pagePath);
}

main();
