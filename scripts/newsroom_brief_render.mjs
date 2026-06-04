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

function newsroomDepthBadgeClass(depth) {
  const d = String(depth || "deep").toLowerCase();
  if (d === "brief") return "depth-badge depth-badge--brief";
  if (d === "major") return "depth-badge depth-badge--major";
  return "depth-badge depth-badge--deep";
}

function newsroomCountStories(data) {
  const front = Array.isArray(data.frontPage) ? data.frontPage.length : 0;
  let dossiers = 0;
  for (const sec of Array.isArray(data.sectorDeepBriefs) ? data.sectorDeepBriefs : []) {
    dossiers += (Array.isArray(sec.storyDossiers) ? sec.storyDossiers : []).length;
  }
  return front + dossiers;
}

function newsroomSourceScanCount(data) {
  const em = data.editorialMeta || {};
  const candidates = [
    em.sourcesScanned,
    em.articlesSelected,
    data.stats && data.stats.articlesCrawled,
  ];
  for (const v of candidates) {
    const n = Number(v);
    if (Number.isFinite(n) && n > 0) return Math.round(n);
  }
  const idx = data.articleLinkIndex;
  return Array.isArray(idx) ? idx.length : 0;
}

function newsroomEstimateReadingMin(data) {
  const chunks = [];
  const push = (s) => {
    const t = String(s || "").trim();
    if (t) chunks.push(t);
  };
  push(data.editorNote);
  for (const fp of Array.isArray(data.frontPage) ? data.frontPage : []) {
    push(fp.title);
    push(fp.oneSentence);
    push(fp.whyItMatters);
    push(fp.watchNext);
  }
  for (const sec of Array.isArray(data.sectorDeepBriefs) ? data.sectorDeepBriefs : []) {
    push(sec.sectorThesis);
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

function buildNewsroomIssueHeader(data) {
  const updated = data.generatedAt ? formatDateVi(data.generatedAt) : "";
  const sources = newsroomSourceScanCount(data);
  const stories = newsroomCountStories(data);
  const readMin = newsroomEstimateReadingMin(data);
  let pills = "";
  if (stories > 0) pills += buildNewsroomStatPill("Stories", String(stories));
  if (sources > 0) pills += buildNewsroomStatPill("Sources", String(sources));
  if (updated) pills += buildNewsroomStatPill("Updated", updated);
  if (readMin > 0) pills += buildNewsroomStatPill("Reading time", `${readMin} phút`);
  return `<header class="issue-header" id="digest-issue-header">
    <span class="issue-badge">48H BRIEF</span>
    <h2 class="issue-title">48h Intelligence Brief</h2>
    <p class="issue-subtitle">Tổng hợp tin tức toàn cầu và Việt Nam</p>
    ${pills ? `<div class="issue-stats">${pills}</div>` : ""}
  </header>`;
}

function buildNewsroomTocHtml(data, sectorSlug) {
  const items = [];
  if (String(data.editorNote || "").trim()) {
    items.push({ id: "digest-editor-note", label: "Lời biên tập" });
  }
  if ((data.frontPage || []).length) {
    items.push({ id: "digest-front-page", label: "Front Page" });
  }
  for (const sec of Array.isArray(data.sectorDeepBriefs) ? data.sectorDeepBriefs : []) {
    const name = String(sec.name || "").trim();
    if (!name) continue;
    items.push({ id: sectorSlug(name), label: newsroomSectorShortLabel(name) });
  }
  if ((data.watchlist2472h || []).length) {
    items.push({ id: "digest-watchlist", label: "Watchlist" });
  }
  if ((data.sourceDesk || []).length) {
    items.push({ id: "digest-source-desk", label: "Source Desk" });
  }
  if (!items.length) return "";
  let html = `<nav class="newsroom-toc-wrap newsroom-toc-wrap--sticky" aria-label="Mục lục bản tin"><div class="newsroom-toc">`;
  for (const it of items) {
    html += `<a class="toc-chip" href="#${escapeHtml(it.id)}">${escapeHtml(it.label)}</a>`;
  }
  html += `</div></nav>`;
  return html;
}

function buildFrontPageCardHtml(fp, variant, buildDossierSourcesHtml) {
  const rank = String(fp.rank || "").trim();
  const rankLabel = rank ? `#${String(rank).padStart(2, "0")}` : "";
  let html = "";
  if (variant === "lead") {
    html += `<article class="front-page-lead">`;
    if (rankLabel) html += `<p class="fp-lead-kicker">Lead · ${escapeHtml(rankLabel)}</p>`;
    html += `<h3>${escapeHtml(fp.title || "")}</h3>`;
    if (fp.oneSentence) html += `<p>${escapeHtml(fp.oneSentence)}</p>`;
    if (fp.whyItMatters) {
      html += `<div class="dossier-block"><p class="dossier-block-label">Vì sao quan trọng</p><p>${escapeHtml(fp.whyItMatters)}</p></div>`;
    }
    if (fp.watchNext) {
      html += `<div class="dossier-block"><p class="dossier-block-label">Theo dõi tiếp</p><p>${escapeHtml(fp.watchNext)}</p></div>`;
    }
    if (fp.links && fp.links.length) {
      html += `<div class="dossier-block"><p class="dossier-block-label">Nguồn đại diện</p>${buildDossierSourcesHtml(fp.links)}</div>`;
    }
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
  html += `<h3 class="pub-section-title">Front Page</h3>`;
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

function buildDossierCardHtml(d, buildDossierSourcesHtml) {
  const depth = String(d.depthLevel || "deep");
  const rank = String(d.rank || "").trim();
  let html = `<div class="dossier-card">`;
  html += `<div class="dossier-head">`;
  html += `<span class="${newsroomDepthBadgeClass(depth)}">${escapeHtml(depth)}</span>`;
  if (rank) html += `<span class="dossier-rank">#${escapeHtml(rank)}</span>`;
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
  const links = Array.isArray(d.links) ? d.links : [];
  if (links.length) {
    html += `<div class="dossier-block"><p class="dossier-block-label">Nguồn đại diện</p>${buildDossierSourcesHtml(links)}</div>`;
  }
  html += `</div>`;
  return html;
}

/**
 * @param {object} data content.json payload
 * @param {{ sectorSlug: (name: string) => string, buildDossierSourcesHtml: (links: unknown[]) => string }} deps
 */
export function buildNewsroomThesisHtml(data, deps) {
  const { sectorSlug, buildDossierSourcesHtml } = deps;
  const editorNote = String(data.editorNote || "").trim();
  const front = Array.isArray(data.frontPage) ? data.frontPage : [];
  const sectors = Array.isArray(data.sectorDeepBriefs) ? data.sectorDeepBriefs : [];
  const watch = Array.isArray(data.watchlist2472h) ? data.watchlist2472h : [];
  const desk = Array.isArray(data.sourceDesk) ? data.sourceDesk : [];

  let html = `<article id="digest-report" class="digest-report newsroom-report">`;
  html += `<div class="digest-main-panel">`;
  html += buildNewsroomIssueHeader(data);
  html += buildNewsroomTocHtml(data, sectorSlug);

  if (editorNote) {
    const paras = editorNote.split(/\n{2,}|\r\n\r\n/).map((p) => p.trim()).filter(Boolean);
    const body =
      paras.length > 1
        ? paras.map((p) => `<p>${escapeHtml(p)}</p>`).join("")
        : `<p class="editor-note-body">${escapeHtml(editorNote)}</p>`;
    html += `<section class="overview-part editor-note-card" id="digest-editor-note">`;
    html += `<p class="eyebrow">Lời biên tập</p>${body}</section>`;
  }

  if (front.length) html += buildNewsroomFrontPageHtml(front, buildDossierSourcesHtml);

  if (sectors.length) {
    html += `<section class="digest-main-sectors overview-part" id="digest-sector-deep">`;
    html += `<h3 class="pub-section-title">Sector deep brief</h3>`;
    for (const sec of sectors) {
      const name = String(sec.name || "").trim() || "Lĩnh vực";
      const code = String(sec.code || "").trim();
      const id = sectorSlug(name);
      const dossiers = Array.isArray(sec.storyDossiers) ? sec.storyDossiers : [];
      html += `<article class="sector-pub-block sector-block" id="${id}">`;
      html += `<header class="sector-pub-head">`;
      html += `<span class="sector-pub-icon" aria-hidden="true">${newsroomSectorIconSvg(code, name)}</span>`;
      html += `<div><h3>${escapeHtml(name)}</h3>`;
      if (dossiers.length) {
        html += `<span class="sector-story-count">${dossiers.length} story</span>`;
      }
      html += `</div></header>`;
      if (sec.sectorThesis) {
        html += `<div class="sector-thesis-card">${escapeHtml(sec.sectorThesis)}</div>`;
      }
      for (const d of dossiers) html += buildDossierCardHtml(d, buildDossierSourcesHtml);
      html += `</article>`;
    }
    html += `</section>`;
  }

  if (watch.length) {
    html += `<section class="overview-part watchlist-panel" id="digest-watchlist">`;
    html += `<h3 class="pub-section-title">Theo dõi 24–72h</h3>`;
    html += `<div class="watchlist-grid">`;
    for (const w of watch) {
      html += `<div class="watch-card">`;
      if (w.theme) html += `<span class="watch-theme">${escapeHtml(w.theme)}</span>`;
      if (w.whatToWatch) {
        html += `<p><strong>Theo dõi:</strong> ${escapeHtml(w.whatToWatch)}</p>`;
      }
      if (w.why) html += `<p class="hint">${escapeHtml(w.why)}</p>`;
      html += `</div>`;
    }
    html += `</div></section>`;
  }

  if (desk.length) {
    html += `<details class="source-desk" id="digest-source-desk">`;
    html += `<summary>Nguồn đại diện theo chủ đề</summary>`;
    html += `<div class="source-desk-body">`;
    for (const g of desk) {
      html += `<div class="source-desk-group">`;
      html += `<h4>${escapeHtml(g.topic || "")}</h4>`;
      html += buildDossierSourcesHtml(g.links);
      html += `</div>`;
    }
    html += `</div></details>`;
  }

  html += `</div></article>`;
  return html;
}
