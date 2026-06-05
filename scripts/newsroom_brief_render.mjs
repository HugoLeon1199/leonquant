/**
 * Newsroom brief HTML renderer (briefMode=newsroom-brief).
 * Shared by embed_public_brief_into_html.mjs — keep in sync with landing_page.html JS.
 */

export function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export function formatDateVi(value) {
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

function newsroomSectorShortLabel(name) {
  const n = String(name || "").toLowerCase();
  if (/kinh tế|tài chính|finance/.test(n)) return "Kinh tế";
  if (/công nghệ|tech|ai/.test(n)) return "Công nghệ";
  if (/thời sự|chính trị|news/.test(n)) return "Thời sự";
  if (/xu hướng|đời sống|trend|lifestyle/.test(n)) return "Đời sống";
  return String(name || "Lĩnh vực").split("&")[0].trim() || "Lĩnh vực";
}

function newsroomSectorIconSvg(code, name) {
  const c = String(code || "").toLowerCase();
  const n = String(name || "").toLowerCase();
  if (c.includes("finance") || /kinh tế|tài chính/.test(n)) {
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19V5M4 19h16M8 15l3-4 3 3 4-6"/></svg>`;
  }
  if (c.includes("tech") || /công nghệ|ai/.test(n)) {
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 9h6v6H9zM12 3v2M12 19v2M3 12h2M19 12h2"/></svg>`;
  }
  if (c.includes("news") || /thời sự|chính trị/.test(n)) {
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M2 12h20M12 2a14 14 0 0 1 0 20M12 2a14 14 0 0 0 0 20"/></svg>`;
  }
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="m12 6 2 5h5l-4 3 1 5-4-3-4 3 1-5-4-3h5z"/></svg>`;
}

function newsroomDepthBadgeLabel(depth) {
  const d = String(depth || "deep").toLowerCase();
  if (d === "brief") return "ngắn";
  if (d === "major") return "nổi bật";
  return "chi tiết";
}

function newsroomDepthBadgeClass(depth) {
  const d = String(depth || "deep").toLowerCase();
  if (d === "brief") return "depth-badge depth-badge--brief";
  if (d === "major") return "depth-badge depth-badge--major";
  return "depth-badge depth-badge--deep";
}

const DIGEST_MAX_NOTABLE = 12;

const EXEC_BRIEF_SECTIONS = [
  ["mainPicture", "Bức tranh chính"],
  ["mostMentioned", "Chủ đề được nhắc nhiều nhất"],
  ["topStories", "Câu chuyện quan trọng nhất"],
  ["sectorImpacts", "Tác động theo khu vực/ngành"],
  ["watch2472h", "Theo dõi 24–72h tới"],
];

function normalizeExternalUrl(url) {
  const u = String(url || "").trim();
  return u.startsWith("http") ? u : "";
}

function getHostName(url) {
  try {
    return (new URL(url).hostname || "").replace(/^www\./i, "");
  } catch {
    return "";
  }
}

function formatSourceLinkLabel(lk, url) {
  const host = lk.host || getHostName(url);
  const src = lk.source || lk.label || "";
  if (host && src) return `${src} · ${host}`;
  return host || src || url;
}

function newsroomCountStories(data) {
  let dossiers = 0;
  for (const sec of Array.isArray(data.sectorDeepBriefs) ? data.sectorDeepBriefs : []) {
    dossiers += (Array.isArray(sec.storyDossiers) ? sec.storyDossiers : []).length;
  }
  return dossiers;
}

function hasStoryLinks(links) {
  return (Array.isArray(links) ? links : []).some((lk) => normalizeExternalUrl(lk?.url));
}

function newsroomArticlesScannedCount(data) {
  const em = data.editorialMeta || {};
  const candidates = [
    em.sourcesScanned,
    data.stats && data.stats.articlesCrawled,
    data.stats && data.stats.articlesInEnriched,
  ];
  for (const v of candidates) {
    const n = Number(v);
    if (Number.isFinite(n) && n > 0) return Math.round(n);
  }
  const idx = data.articleLinkIndex;
  return Array.isArray(idx) ? idx.length : 0;
}

function newsroomBriefSelectedCount(data) {
  const sel = Number(data.editorialMeta?.articlesSelected);
  if (Number.isFinite(sel) && sel > 0) return Math.round(sel);
  return newsroomCountStories(data);
}

/** @returns {string} Vietnamese provenance line (no trailing period). */
export function buildNewsroomSourceProvenanceText(data) {
  const scanned = newsroomArticlesScannedCount(data);
  const selected = newsroomBriefSelectedCount(data);
  if (!scanned && !selected) return "";
  const fmt = (n) => n.toLocaleString("vi-VN");
  const bits = [];
  if (scanned > 0) {
    bits.push(`tổng hợp từ khoảng ${fmt(scanned)} bài báo đã quét trong 48 giờ`);
  }
  if (selected > 0) {
    bits.push(`chọn lọc thành ${fmt(selected)} tin chính trong bản tin`);
  }
  return bits.join(" · ");
}

export function buildNewsroomSyncNoteText(_data) {
  return "";
}

function newsroomEstimateReadingMin(data) {
  const chunks = [];
  const push = (s) => {
    const t = String(s || "").trim();
    if (t) chunks.push(t);
  };
  push(data.editorNote);
  const eb = data.executiveBriefing || {};
  push(eb.title);
  push(eb.content);
  (eb.watchNext || []).forEach(push);
  for (const row of eb.mostMentionedTopics || []) {
    push(row.topic);
    push(row.whyMentioned);
    push(row.evidenceHint);
  }
  for (const row of eb.hottestTopics || []) {
    push(row.topic);
    push(row.whyHot);
    push(row.impact);
    push(row.evidenceHint);
  }
  for (const row of eb.emergingSignals || []) {
    push(row.signal);
    push(row.whyWatch);
  }
  for (const fp of Array.isArray(data.frontPage) ? data.frontPage : []) {
    push(fp.title);
    push(fp.oneSentence);
    push(fp.whyItMatters);
    push(fp.watchNext);
  }
  for (const sec of Array.isArray(data.sectorDeepBriefs) ? data.sectorDeepBriefs : []) {
    push(sec.sectorThesis);
    for (const sb of Array.isArray(sec.subsectorBriefs) ? sec.subsectorBriefs : []) {
      push(sb.name);
      push(sb.overview);
      (sb.keyPoints || []).forEach(push);
    }
    for (const d of Array.isArray(sec.storyDossiers) ? sec.storyDossiers : []) {
      push(d.title);
      push(d.summary);
      push(d.whyItMatters);
      (d.mainDevelopments || []).forEach(push);
      (d.affectedGroups || []).forEach(push);
      (d.watchNext || []).forEach(push);
    }
  }
  for (const w of Array.isArray(data.watchlist2472h) ? data.watchlist2472h : []) {
    push(w.theme);
    push(w.whatToWatch);
    push(w.why);
  }
  const chars = chunks.join(" ").length;
  if (!chars) return 0;
  return Math.max(3, Math.round(chars / 900));
}

function buildNewsroomStatPill(label, value) {
  const v = value == null || value === "" ? "" : String(value).trim();
  if (!v) return "";
  return `<span class="stat-pill">${escapeHtml(label)}: <strong>${escapeHtml(v)}</strong></span>`;
}

function buildNewsroomIssueHeader(_data) {
  return `<header class="issue-header issue-header--minimal" id="digest-issue-header">
    <h2 class="issue-title">Bản tin 48h</h2>
  </header>`;
}

function collectSectorLinks(sec) {
  const out = [];
  const seen = new Set();
  const add = (lk) => {
    const u = normalizeExternalUrl(lk?.url);
    if (!u || seen.has(u)) return;
    seen.add(u);
    out.push(lk);
  };
  for (const lk of Array.isArray(sec.links) ? sec.links : []) add(lk);
  for (const sb of Array.isArray(sec.subsectorBriefs) ? sec.subsectorBriefs : []) {
    for (const lk of Array.isArray(sb.links) ? sb.links : []) add(lk);
  }
  for (const d of Array.isArray(sec.storyDossiers) ? sec.storyDossiers : []) {
    for (const lk of Array.isArray(d.links) ? d.links : []) add(lk);
  }
  return out;
}

function buildSectorArticleLinksHtml(links) {
  const rows = (Array.isArray(links) ? links : []).filter((lk) => normalizeExternalUrl(lk?.url));
  if (!rows.length) return "";
  let html = `<div class="sector-article-links">`;
  for (const lk of rows) {
    const u = normalizeExternalUrl(lk.url);
    const title = escapeHtml(lk.title || u);
    const excerpt = String(lk.excerpt || "").trim();
    html += `<article class="sector-article-link">`;
    html += `<a class="sector-article-link-title" href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">${title}</a>`;
    if (excerpt) {
      const paras = excerpt.split(/\n{2,}|\r\n\r\n/).map((p) => p.trim()).filter(Boolean);
      if (paras.length > 1) {
        for (const p of paras) html += `<p class="sector-article-link-excerpt">${escapeHtml(p)}</p>`;
      } else {
        html += `<p class="sector-article-link-excerpt">${escapeHtml(excerpt)}</p>`;
      }
    }
    html += `</article>`;
  }
  html += `</div>`;
  return html;
}

function executiveBriefingHasBody(briefing) {
  const b = briefing && typeof briefing === "object" ? briefing : {};
  if (String(b.content || "").trim()) return true;
  const sec = b.sections && typeof b.sections === "object" ? b.sections : {};
  return EXEC_BRIEF_SECTIONS.some(([key]) => String(sec[key] || "").trim());
}

function buildRepresentativeSourcesHtml(links) {
  const rows = (Array.isArray(links) ? links : []).filter((lk) => lk && normalizeExternalUrl(lk.url));
  if (!rows.length) return "";
  let inner = `<div class="dossier-source-links">`;
  for (const lk of rows) {
    const u = normalizeExternalUrl(lk.url);
    if (!u) continue;
    const srcLabel = escapeHtml(formatSourceLinkLabel(lk, u));
    inner += `<a class="sector-topic-source" href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">${srcLabel}</a>`;
  }
  inner += `</div>`;
  return `<div class="representative-sources-block"><p class="dossier-block-label">Nguồn tiêu biểu</p>${inner}</div>`;
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
    .filter((a) => a && normalizeExternalUrl(a.url))
    .slice(0, DIGEST_MAX_NOTABLE);
  if (!items.length) {
    return `<p class="hint">Chưa có tin nổi bật trong bản digest hôm nay.</p>`;
  }
  let h = `<div class="notable-list">`;
  items.forEach((a, idx) => {
    const u = normalizeExternalUrl(a.url);
    const title = escapeHtml(a.title || u);
    const meta = escapeHtml([a.source, a.host || getHostName(u)].filter(Boolean).join(" · "));
    const img = String(a.imageUrl || a.image_url || imageByUrl.get(u) || "").trim();
    const why = escapeHtml(String(a.whyNotable || "").trim());
    const hostShort = escapeHtml((a.host || getHostName(u) || "WEB").replace(/^www\./i, "").slice(0, 8));
    const rank = String(idx + 1).padStart(2, "0");
    h += `<a class="notable-item" href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">`;
    h += `<span class="notable-item-rank">${rank}</span>`;
    if (img) {
      h += `<span class="notable-item-thumb"><img src="${escapeHtml(img)}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.parentElement.remove()"></span>`;
    } else {
      h += `<span class="notable-item-thumb notable-item-thumb--ph" aria-hidden="true">${hostShort}</span>`;
    }
    h += `<span class="notable-item-body">`;
    h += `<span class="notable-item-title">${title}</span>`;
    if (meta) h += `<span class="notable-item-meta">${meta}</span>`;
    if (why) h += `<span class="notable-item-why">${why}</span>`;
    h += `</span></a>`;
  });
  h += `</div>`;
  return h;
}

function buildArticleArchiveHtml(articles) {
  const rows = (Array.isArray(articles) ? articles : []).filter((a) => normalizeExternalUrl(a?.url));
  if (!rows.length) return "";
  const nLabel = rows.length.toLocaleString("vi-VN");
  let h = `<details class="article-archive-wrap digest-notable-all">`;
  h += `<summary>Bản tin được tổng hợp từ ${nLabel} bài, bấm vào xem chi tiết</summary>`;
  h += `<div class="article-archive-scroll"><ul class="link-rows">`;
  for (const L of rows) {
    const u = normalizeExternalUrl(L.url);
    if (!u) continue;
    const title = escapeHtml(L.title || L.host || u);
    const meta = escapeHtml([L.source, L.host].filter(Boolean).join(" · "));
    h += `<li><a href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">${title}</a>`;
    if (meta) h += `<span class="link-meta">${meta}</span>`;
    h += `</li>`;
  }
  h += `</ul></div></details>`;
  return h;
}

function buildNewsroomFeedSection(data) {
  const notable = Array.isArray(data.digestNotableArticles) ? data.digestNotableArticles : [];
  const articles = Array.isArray(data.articleLinkIndex) ? data.articleLinkIndex : [];
  if (!notable.length && !articles.length) return "";
  const imageByUrl = buildArticleImageLookup(data);
  let html = `<section class="overview-part digest-report-extra" id="digest-main--notable">`;
  html += `<h3 class="pub-section-title">Tin đáng chú ý</h3>`;
  html += buildNotableCardsHtml(notable, imageByUrl);
  html += buildArticleArchiveHtml(articles);
  html += `</section>`;
  return html;
}

function buildNewsroomTocHtml(_data, _sectorSlug) {
  return "";
}

function buildExecutiveBriefingHtml(briefing, editorNote) {
  const b = briefing && typeof briefing === "object" ? briefing : {};
  const sections = b.sections && typeof b.sections === "object" ? b.sections : {};
  const content = String(b.content || "").trim();
  const editor = String(editorNote || "").trim();
  const hasSections = EXEC_BRIEF_SECTIONS.some(([key]) => String(sections[key] || "").trim());
  if (!content && !hasSections && !editor) return "";

  const title = "Tổng quan 48h";
  let html = `<section class="overview-part executive-briefing-card" id="digest-executive-briefing">`;
  html += `<h3 class="pub-section-title">${escapeHtml(title)}</h3>`;
  html += `<div class="executive-briefing-body">`;

  if (editor) {
    const editorParas = editor.split(/\n{2,}|\r\n\r\n/).map((p) => p.trim()).filter(Boolean);
    if (editorParas.length > 1) {
      for (const p of editorParas) html += `<p class="executive-brief-lead">${escapeHtml(p)}</p>`;
    } else {
      html += `<p class="executive-brief-lead">${escapeHtml(editor)}</p>`;
    }
  }

  if (hasSections) {
    for (const [key, label] of EXEC_BRIEF_SECTIONS) {
      const body = String(sections[key] || "").trim();
      if (!body) continue;
      const paras = body.split(/\n{2,}|\r\n\r\n/).map((p) => p.trim()).filter(Boolean);
      html += `<div class="executive-brief-section"><h4 class="executive-brief-heading">${escapeHtml(label)}</h4>`;
      if (paras.length > 1) {
        for (const p of paras) html += `<p>${escapeHtml(p)}</p>`;
      } else {
        html += `<p>${escapeHtml(body)}</p>`;
      }
      html += `</div>`;
    }
  } else {
    const paras = content.split(/\n{2,}|\r\n\r\n/).map((p) => p.trim()).filter(Boolean);
    if (paras.length > 1) {
      for (const p of paras) html += `<p>${escapeHtml(p)}</p>`;
    } else if (content) {
      html += `<p>${escapeHtml(content)}</p>`;
    }
    const most = Array.isArray(b.mostMentionedTopics) ? b.mostMentionedTopics : [];
    if (most.length) {
      html += `<div class="executive-brief-section"><h4 class="executive-brief-heading">Chủ đề được nhắc nhiều nhất</h4><ul class="sector-points prose-bullets">`;
      for (const t of most.slice(0, 6)) {
        const topic = String(t.topic || "").trim();
        if (!topic) continue;
        const why = String(t.whyMentioned || "").trim();
        html += `<li><strong>${escapeHtml(topic)}</strong>${why ? `: ${escapeHtml(why)}` : ""}</li>`;
      }
      html += `</ul></div>`;
    }
    const hot = Array.isArray(b.hottestTopics) ? b.hottestTopics : [];
    if (hot.length) {
      html += `<div class="executive-brief-section"><h4 class="executive-brief-heading">Câu chuyện quan trọng nhất</h4><ul class="sector-points prose-bullets">`;
      for (const t of hot.slice(0, 6)) {
        const topic = String(t.topic || "").trim();
        if (!topic) continue;
        const why = String(t.whyHot || "").trim();
        html += `<li><strong>${escapeHtml(topic)}</strong>${why ? `: ${escapeHtml(why)}` : ""}</li>`;
      }
      html += `</ul></div>`;
    }
    const wn = Array.isArray(b.watchNext) ? b.watchNext : [];
    if (wn.length) {
      html += `<div class="executive-brief-section"><h4 class="executive-brief-heading">Theo dõi 24–72h tới</h4><ul class="sector-points prose-bullets">`;
      for (const t of wn.slice(0, 8)) html += `<li>${escapeHtml(t)}</li>`;
      html += `</ul></div>`;
    }
  }

  html += `</div>`;
  const briefLinks = Array.isArray(b.links) ? b.links : [];
  if (briefLinks.length) html += buildRepresentativeSourcesHtml(briefLinks);
  html += `</section>`;
  return html;
}

function buildFrontPageCardHtml(fp, variant, buildDossierSourcesHtml) {
  const rank = String(fp.rank || "").trim();
  const rankLabel = rank ? `#${String(rank).padStart(2, "0")}` : "";
  let html = "";
  if (variant === "lead") {
    html += `<article class="front-page-lead">`;
    if (rankLabel) html += `<p class="fp-lead-kicker">Điểm nóng · ${escapeHtml(rankLabel)}</p>`;
    html += `<h3>${escapeHtml(fp.title || "")}</h3>`;
    if (fp.oneSentence) html += `<p>${escapeHtml(fp.oneSentence)}</p>`;
    if (fp.whyItMatters) {
      html += `<div class="dossier-block"><p class="dossier-block-label">Vì sao quan trọng</p><p>${escapeHtml(fp.whyItMatters)}</p></div>`;
    }
    if (fp.watchNext) {
      html += `<div class="dossier-block"><p class="dossier-block-label">Theo dõi tiếp</p><p>${escapeHtml(fp.watchNext)}</p></div>`;
    }
    if (fp.links && fp.links.length) html += buildDossierSourcesHtml(fp.links);
    html += `</article>`;
    return html;
  }
  const cls =
    variant === "compact" ? "front-page-card front-page-card--compact" : "front-page-card";
  html += `<div class="${cls}">`;
  if (rankLabel) html += `<span class="fp-rank">${escapeHtml(rankLabel)}</span>`;
  html += `<h4>${escapeHtml(fp.title || "")}</h4>`;
  if (fp.oneSentence) html += `<p>${escapeHtml(fp.oneSentence)}</p>`;
  if (fp.watchNext) {
    html += `<p class="hint">${escapeHtml(String(fp.watchNext).slice(0, 220))}</p>`;
  }
  if (fp.links && fp.links.length) html += buildDossierSourcesHtml(fp.links);
  html += `</div>`;
  return html;
}

function buildNewsroomFrontPageHtml(front, buildDossierSourcesHtml) {
  const sorted = [...front].sort(
    (a, b) => (Number(a.rank) || 999) - (Number(b.rank) || 999),
  );
  const lead = sorted.find((x) => Number(x.rank) === 1) || sorted[0];
  const rest = sorted.filter((x) => x !== lead);
  const secondary = rest.filter((x) => {
    const r = Number(x.rank);
    return r >= 2 && r <= 5;
  });
  const compact = rest.filter((x) => !secondary.includes(x));
  let html = `<section class="overview-part" id="digest-front-page">`;
  html += `<h3 class="pub-section-title">Điểm nóng</h3>`;
  if (lead) html += buildFrontPageCardHtml(lead, "lead", buildDossierSourcesHtml);
  if (secondary.length) {
    html += `<div class="front-page-secondary-grid">`;
    for (const fp of secondary) html += buildFrontPageCardHtml(fp, "secondary", buildDossierSourcesHtml);
    html += `</div>`;
  }
  if (compact.length) {
    html += `<ul class="front-page-compact-list">`;
    for (const fp of compact) {
      html += `<li>${buildFrontPageCardHtml(fp, "compact", buildDossierSourcesHtml)}</li>`;
    }
    html += `</ul>`;
  }
  html += `</section>`;
  return html;
}

function buildDossierCardHtml(d) {
  const depth = String(d.depthLevel || "deep");
  const rank = String(d.rank || "").trim();
  let html = `<div class="dossier-card">`;
  html += `<div class="dossier-head">`;
  html += `<span class="${newsroomDepthBadgeClass(depth)}">${escapeHtml(newsroomDepthBadgeLabel(depth))}</span>`;
  if (rank) html += `<span class="dossier-rank">#${escapeHtml(rank)}</span>`;
  if (d.subSector) html += `<span class="chip chip--subsector">${escapeHtml(d.subSector)}</span>`;
  html += `</div>`;
  html += `<h4>${escapeHtml(d.title || "")}</h4>`;
  if (d.summary) html += `<p class="dossier-summary">${escapeHtml(d.summary)}</p>`;
  const devs = Array.isArray(d.mainDevelopments) ? d.mainDevelopments : [];
  if (devs.length) {
    html += `<div class="dossier-block"><p class="dossier-block-label">Diễn biến chính</p>`;
    html += `<ul class="sector-points prose-bullets">`;
    for (const line of devs) html += `<li>${escapeHtml(line)}</li>`;
    html += `</ul></div>`;
  }
  if (d.whyItMatters) {
    html += `<div class="dossier-block"><p class="dossier-block-label">Vì sao quan trọng</p><p>${escapeHtml(d.whyItMatters)}</p></div>`;
  }
  const ag = Array.isArray(d.affectedGroups) ? d.affectedGroups : [];
  if (ag.length) {
    html += `<div class="dossier-block"><p class="dossier-block-label">Nhóm ảnh hưởng</p><div class="chip-row">`;
    for (const g of ag) html += `<span class="chip">${escapeHtml(g)}</span>`;
    html += `</div></div>`;
  }
  const wn = Array.isArray(d.watchNext) ? d.watchNext : [];
  if (wn.length) {
    html += `<div class="dossier-block"><p class="dossier-block-label">Theo dõi tiếp</p><div class="chip-row">`;
    for (const line of wn) html += `<span class="chip">${escapeHtml(line)}</span>`;
    html += `</div></div>`;
  }
  if (hasStoryLinks(d.links)) html += buildRepresentativeSourcesHtml(d.links);
  html += `</div>`;
  return html;
}

/**
 * @param {object} data content.json payload
 * @param {{ sectorSlug: (name: string) => string, buildDossierSourcesHtml: (links: unknown[]) => string }} deps
 */
export function buildNewsroomThesisHtml(data, deps) {
  const { sectorSlug } = deps;
  const editorNote = String(data.editorNote || "").trim();
  const sectors = Array.isArray(data.sectorDeepBriefs) ? data.sectorDeepBriefs : [];
  const executiveBriefing = data.executiveBriefing || {};

  let html = `<article id="digest-report" class="digest-report newsroom-report">`;
  html += `<div class="digest-main-panel">`;
  html += buildNewsroomIssueHeader(data);
  html += buildNewsroomTocHtml(data, sectorSlug);
  html += buildExecutiveBriefingHtml(executiveBriefing, editorNote);

  if (sectors.length) {
    html += `<section class="digest-main-sectors overview-part" id="digest-sector-deep">`;
    html += `<h3 class="pub-section-title">Đi sâu theo từng ngành</h3>`;
    let sectorIndex = 0;
    for (const sec of sectors) {
      const name = String(sec.name || "").trim() || "Lĩnh vực";
      const thesis = String(sec.sectorThesis || "").trim();
      const links = collectSectorLinks(sec);
      if (!thesis && !links.length) continue;
      sectorIndex += 1;
      const id = sectorSlug(name);
      html += `<article class="sector-simple-block" id="${id}">`;
      html += `<h3 class="sector-simple-title"><span class="sector-simple-num">${sectorIndex}.</span> ${escapeHtml(name)}</h3>`;
      if (thesis) {
        const paras = thesis.split(/\n{2,}|\r\n\r\n/).map((p) => p.trim()).filter(Boolean);
        html += `<div class="sector-simple-body">`;
        if (paras.length > 1) {
          for (const p of paras) html += `<p>${escapeHtml(p)}</p>`;
        } else {
          html += `<p>${escapeHtml(thesis)}</p>`;
        }
        html += `</div>`;
      }
      html += buildSectorArticleLinksHtml(links);
      html += `</article>`;
    }
    html += `</section>`;
  }

  html += buildNewsroomFeedSection(data);
  html += `</div></article>`;
  return html;
}
