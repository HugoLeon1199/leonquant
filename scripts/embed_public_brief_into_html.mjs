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
  const wc = (Array.isArray(data.whatChanged) ? data.whatChanged : []).filter((r) => r && typeof r === "object");
  const mscore = data.marketRegimeScore || {};
  const mItems = Array.isArray(mscore.items) ? mscore.items : [];
  const im = (Array.isArray(data.intermarketMap) ? data.intermarketMap : []).filter((r) => r && typeof r === "object");
  const chains = Array.isArray(data.transmissionChains) ? data.transmissionChains : [];
  const qa = (Array.isArray(data.quickActions) ? data.quickActions : []).filter((r) => r && typeof r === "object");
  const ag = (Array.isArray(data.allocationGuide) ? data.allocationGuide : []).filter((r) => r && typeof r === "object");
  const pa = data.priorityAndAvoid || {};
  const pri = Array.isArray(pa.prioritize) ? pa.prioritize : [];
  const avo = Array.isArray(pa.avoidOrBeCareful) ? pa.avoidOrBeCareful : [];
  const ir = (Array.isArray(data.increaseRiskSignals) ? data.increaseRiskSignals : []).filter(
    (r) => r && typeof r === "object",
  );
  const rr = (Array.isArray(data.reduceRiskSignals) ? data.reduceRiskSignals : []).filter(
    (r) => r && typeof r === "object",
  );
  const ip = (Array.isArray(data.intradayPlaybook) ? data.intradayPlaybook : []).filter((r) => r && typeof r === "object");
  const scen = data.scenarioPlan || {};
  const vct = data.viewChangeTriggers || {};
  const mp = Array.isArray(vct.morePositiveIf) ? vct.morePositiveIf : [];
  const mn = Array.isArray(vct.moreNegativeIf) ? vct.moreNegativeIf : [];
  const marketImpact = (d) => String(d.marketImpact || d.vietnamImpact || ND);

  let thesisHtml = "";
  thesisHtml += `<div class="section-head"><p class="eyebrow">Luận điểm</p><h2>Luận điểm chính hôm nay</h2></div>`;
  thesisHtml += `<div class="thesis-block">`;
  thesisHtml += `<p class="lbl">Trạng thái / nhịp thị trường</p><p>${escapeHtml(mt.regime || ND)}</p>`;
  thesisHtml += `<p class="lbl">Luận điểm</p><p>${escapeHtml(mt.thesis || ND)}</p>`;
  thesisHtml += `<p class="lbl">Kết luận hành động</p><p>${escapeHtml(mt.actionConclusion || ND)}</p>`;
  thesisHtml += `</div>`;

  let whatChangedHtml = "";
  whatChangedHtml += `<div class="section-head"><p class="eyebrow">Thay đổi</p><h2>Điều thay đổi quan trọng</h2></div>`;
  if (!wc.length) {
    whatChangedHtml += `<p class="error-card">Chưa có mục thay đổi.</p>`;
  } else {
    whatChangedHtml += renderTable(
      ["Biến số", "Diễn biến", "Ý nghĩa"],
      wc.map((r) => [
        escapeHtml(r.variable || ND),
        escapeHtml(r.change || ND),
        escapeHtml(r.meaning || ND),
      ]),
    );
  }

  let regimeHtml = "";
  regimeHtml += `<div class="section-head"><p class="eyebrow">Regime</p><h2>Market Regime Score</h2></div>`;
  regimeHtml += `<div class="thesis-block compact-regime">`;
  regimeHtml += `<p><span class="lbl">Tổng điểm</span> ${escapeHtml(String(mscore.totalScore ?? ND))} · `;
  regimeHtml += `<span class="lbl">Nhãn</span> ${escapeHtml(mscore.regime || ND)}</p>`;
  regimeHtml += `<p class="body">${escapeHtml(mscore.interpretation || ND)}</p>`;
  regimeHtml += `</div>`;
  if (mItems.length) {
    regimeHtml += renderTable(
      ["Trục", "Tín hiệu", "Điểm"],
      mItems.map((r) => [escapeHtml(r.axis || ND), escapeHtml(r.signal || ND), escapeHtml(String(r.score ?? ND))]),
    );
  }

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
      macroHtml += `<p class="sub">Tác động liên thị trường</p><p class="body">${escapeHtml(marketImpact(d))}</p></article>`;
    }
    macroHtml += `</div>`;
  }

  let interHtml = "";
  interHtml += `<div class="section-head"><p class="eyebrow">Liên thị trường</p><h2>Bản đồ liên thị trường</h2></div>`;
  if (!im.length) {
    interHtml += `<p class="error-card">Chưa có bản đồ liên thị trường.</p>`;
  } else {
    interHtml += renderTable(
      ["Tài sản", "Trạng thái", "Gợi ý xử lý"],
      im.map((r) => [
        escapeHtml(r.asset || ND),
        escapeHtml(r.state || ND),
        escapeHtml(r.action || ND),
      ]),
    );
  }

  let transmissionHtml = "";
  transmissionHtml += `<div class="section-head"><p class="eyebrow">Truyền dẫn</p><h2>Chuỗi truyền dẫn vào danh mục</h2></div>`;
  if (chains.length) {
    transmissionHtml += `<ul class="chain-list">`;
    for (const c of chains) transmissionHtml += `<li>${escapeHtml(c)}</li>`;
    transmissionHtml += `</ul>`;
  } else {
    transmissionHtml += `<p class="error-card">Chưa có chuỗi truyền dẫn.</p>`;
  }

  let actionsHtml = "";
  actionsHtml += `<div class="section-head"><p class="eyebrow">Thực thi</p><h2>Hành động nhanh hôm nay</h2></div>`;
  actionsHtml += renderTable(
    ["Trạng thái nhà đầu tư", "Hành động phù hợp"],
    qa.map((r) => [escapeHtml(r.investorState || ND), escapeHtml(r.action || ND)]),
  );

  let allocationHtml = "";
  allocationHtml += `<div class="section-head"><p class="eyebrow">Danh mục</p><h2>Phân bổ vốn tham khảo</h2></div>`;
  allocationHtml += renderTable(
    ["Hồ sơ rủi ro", "Cổ phiếu", "Tiền mặt", "Vàng / phòng thủ", "Crypto (rủi ro cao)", "Đòn bẩy"],
    ag.map((r) => [
      escapeHtml(r.profile || ND),
      escapeHtml(r.stocks || ND),
      escapeHtml(r.cash || ND),
      escapeHtml(r.goldDefense || ND),
      escapeHtml(r.cryptoHighRisk || ND),
      escapeHtml(r.leverage || r.margin || ND),
    ]),
  );

  let priorityHtml = "";
  priorityHtml += `<div class="section-head"><p class="eyebrow">Ưu tiên</p><h2>Ưu tiên và thận trọng</h2></div>`;
  priorityHtml += `<h3 class="subhead">Ưu tiên</h3>`;
  priorityHtml += renderTable(
    ["Hạng mục", "Lý do"],
    pri.filter((r) => r && typeof r === "object").map((r) => [escapeHtml(r.asset || ND), escapeHtml(r.reason || ND)]),
  );
  priorityHtml += `<h3 class="subhead" style="margin-top:20px">Thận trọng / hạn chế</h3>`;
  priorityHtml += renderTable(
    ["Hạng mục", "Lý do"],
    avo.filter((r) => r && typeof r === "object").map((r) => [escapeHtml(r.asset || ND), escapeHtml(r.reason || ND)]),
  );

  let riskOnHtml = "";
  riskOnHtml += `<div class="section-head"><p class="eyebrow">Tăng rủi ro</p><h2>Tín hiệu để tăng rủi ro</h2></div>`;
  riskOnHtml += renderTable(
    ["Tín hiệu", "Ý nghĩa"],
    ir.map((r) => [escapeHtml(r.signal || ND), escapeHtml(r.meaning || ND)]),
  );

  let riskOffHtml = "";
  riskOffHtml += `<div class="section-head"><p class="eyebrow">Giảm rủi ro</p><h2>Tín hiệu cần giảm rủi ro</h2></div>`;
  riskOffHtml += renderTable(
    ["Tín hiệu cảnh báo", "Hành động"],
    rr.map((r) => [escapeHtml(r.signal || ND), escapeHtml(r.action || ND)]),
  );

  let intradayHtml = "";
  intradayHtml += `<div class="section-head"><p class="eyebrow">Phiên</p><h2>Playbook trong phiên</h2></div>`;
  intradayHtml += renderTable(
    ["Điều kiện hành vi", "Gợi ý"],
    ip.map((r) => [escapeHtml(r.marketCondition || ND), escapeHtml(r.action || ND)]),
  );

  let scenariosHtml = "";
  scenariosHtml += `<div class="section-head"><p class="eyebrow">Kịch bản</p><h2>Kịch bản thị trường</h2></div>`;
  const b = scen.baseCase || {};
  const u = scen.bullCase || {};
  const e = scen.bearCase || {};
  scenariosHtml += `<div class="scenario-grid">`;
  scenariosHtml += `<article class="sc"><h3>${escapeHtml(b.title || "Kịch bản cơ sở")}</h3><p>${escapeHtml(b.description || ND)}</p><p class="sub" style="margin-top:12px">Hành động</p><p>${escapeHtml(b.action || ND)}</p></article>`;
  scenariosHtml += `<article class="sc bull"><h3>${escapeHtml(u.title || "Kịch bản tích cực")}</h3><p>${escapeHtml(u.description || ND)}</p><p class="sub" style="margin-top:12px">Hành động</p><p>${escapeHtml(u.action || ND)}</p></article>`;
  scenariosHtml += `<article class="sc bear"><h3>${escapeHtml(e.title || "Kịch bản tiêu cực")}</h3><p>${escapeHtml(e.description || ND)}</p><p class="sub" style="margin-top:12px">Hành động</p><p>${escapeHtml(e.action || ND)}</p></article>`;
  scenariosHtml += `</div>`;

  let triggersHtml = "";
  triggersHtml += `<div class="section-head"><p class="eyebrow">Theo dõi</p><h2>Điều gì sẽ làm thay đổi quan điểm?</h2></div>`;
  triggersHtml += `<div class="two-col-triggers">`;
  triggersHtml += `<div><p class="sub">Thiên lệch tích cực hơn nếu</p><ul class="chain-list">`;
  for (const t of mp) triggersHtml += `<li>${escapeHtml(t)}</li>`;
  triggersHtml += `</ul></div><div><p class="sub">Thiên lệch tiêu cực hơn nếu</p><ul class="chain-list">`;
  for (const t of mn) triggersHtml += `<li>${escapeHtml(t)}</li>`;
  triggersHtml += `</ul></div></div>`;

  let finalHtml = "";
  finalHtml += `<div class="section-head"><p class="eyebrow">Đóng phiên</p><h2>Câu quyết định cuối cùng</h2></div>`;
  finalHtml += `<div class="takeaway"><p>${escapeHtml(data.finalDecision || ND)}</p></div>`;

  return {
    thesis: thesisHtml,
    whatChanged: whatChangedHtml,
    regime: regimeHtml,
    macro: macroHtml,
    intermarket: interHtml,
    transmission: transmissionHtml,
    actions: actionsHtml,
    allocation: allocationHtml,
    priority: priorityHtml,
    riskOn: riskOnHtml,
    riskOff: riskOffHtml,
    intraday: intradayHtml,
    scenarios: scenariosHtml,
    triggers: triggersHtml,
    finalDecision: finalHtml,
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
  const digestMode = data.briefMode === "multisector-digest";
  if (digestMode) {
    if (/<body\s+class="/i.test(html)) {
      html = html.replace(/<body\s+class="([^"]*)"/i, '<body class="$1 digest-mode"');
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

function syncNoteHtml(generatedAt, digestMode) {
  const st = generatedAt ? formatDateVi(generatedAt) : "";
  if (!st) return `<p id="syncNote" class="sync-note"></p>`;
  if (digestMode) {
    return `<p id="syncNote" class="sync-note">Tin tức được tổng hợp lúc ${escapeHtml(st)}.</p>`;
  }
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
  const digestMode = data.briefMode === "multisector-digest";
  const parts = digestMode ? {} : buildBriefParts(data);
  const ids = [
    "sectionLinkIndex",
    "sectionThesis",
    "sectionWhatChanged",
    "sectionRegimeScore",
    "sectionMacro",
    "sectionIntermarket",
    "sectionTransmission",
    "sectionActions",
    "sectionAllocation",
    "sectionPriority",
    "sectionRiskOn",
    "sectionRiskOff",
    "sectionIntraday",
    "sectionScenarios",
    "sectionViewTriggers",
    "sectionFinalDecision",
  ];
  const keys = [
    "linkIndex",
    "thesis",
    "whatChanged",
    "regime",
    "macro",
    "intermarket",
    "transmission",
    "actions",
    "allocation",
    "priority",
    "riskOn",
    "riskOff",
    "intraday",
    "scenarios",
    "triggers",
    "finalDecision",
  ];

  let html = fs.readFileSync(pagePath, "utf8");
  html = updateHero(html, data);

  if (!digestMode) {
    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      const inner = parts[keys[i]] || "";
      const pattern = `<div\\s+id="${id}"\\s+class="brief-block"\\s*>\\s*</div>`;
      if (!new RegExp(pattern, "i").test(html)) {
        console.error(`Placeholder not found for #${id}; brief-block must be empty in source HTML.`);
        process.exit(1);
      }
      html = html.replace(
        new RegExp(pattern, "gi"),
        `<div id="${id}" class="brief-block">${inner}</div>`,
      );
    }
  }

  const articles = Array.isArray(data.allArticles) ? data.allArticles : [];
  const gridInner = digestMode ? "" : buildArticleCardsHtml(articles);
  const gridPattern = `<div\\s+id="sourceGrid"\\s+class="source-grid"\\s*>\\s*</div>`;
  if (!new RegExp(gridPattern, "i").test(html)) {
    console.error('Placeholder not found for #sourceGrid (empty source-grid div).');
    process.exit(1);
  }
  html = html.replace(
    new RegExp(gridPattern, "gi"),
    `<div id="sourceGrid" class="source-grid" data-embedded-articles="1">${gridInner}</div>`,
  );
  html = html.replace(
    `<h2 id="sourceGridTitle">Tin nền tham khảo</h2>`,
    `<h2 id="sourceGridTitle">Tin nền tham khảo (${articles.length})</h2>`,
  );

  html = html.replace(
    /<p id="syncNote" class="sync-note"><\/p>/,
    syncNoteHtml(data.generatedAt, digestMode),
  );

  html = html.replace('<section id="brief" class="alt">', '<section id="brief" class="alt" data-embedded-brief="1">');

  fs.writeFileSync(pagePath, html, "utf8");
  console.log("Embedded brief + articles into", pagePath);
}

main();
