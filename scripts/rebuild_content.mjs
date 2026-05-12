/**
 * Dựng content.json từ final_summary.json + enriched khi không có Python.
 * Sanitize logic khớp build_website_content.sanitize_strategy_brief_snake.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");

const SAFE_ALLOCATION_GUIDE = [
  { profile: "Thận trọng", stocks: "30–40%", cash: "60–70%", margin: "Không dùng" },
  { profile: "Cân bằng", stocks: "50–60%", cash: "40–50%", margin: "Rất thấp" },
  {
    profile: "Chủ động",
    stocks: "60–70%",
    cash: "30–40%",
    margin: "Chỉ dùng khi thị trường xác nhận",
  },
];

const SAFE_ACTION_CONCLUSION =
  "Không cần rút lui hoàn toàn, nhưng cũng không nên mua đuổi. Chiến lược phù hợp là giữ tỷ trọng vừa phải, " +
  "ưu tiên cổ phiếu khỏe, hạn chế margin và chờ xác nhận từ dòng tiền.";

const SAFE_INCREASE_RISK_SIGNALS = [
  { signal: "VN-Index tăng cùng thanh khoản cải thiện", meaning: "Dòng tiền thật quay lại." },
  { signal: "Số mã tăng lan rộng", meaning: "Độ rộng thị trường khỏe hơn." },
  { signal: "Ngân hàng giữ vai trò dẫn dắt", meaning: "Chỉ số có trụ đỡ tốt hơn." },
  { signal: "Khối ngoại giảm bán hoặc mua ròng", meaning: "Áp lực vốn ngoại hạ nhiệt." },
  { signal: "USD/VND ổn định", meaning: "Rủi ro tỷ giá giảm." },
  { signal: "Cổ phiếu vượt nền với volume tốt", meaning: "Có điểm mua rõ hơn." },
];

const SAFE_REDUCE_RISK_SIGNALS = [
  { signal: "VN-Index tăng nhưng độ rộng yếu", action: "Không mua đuổi." },
  { signal: "Thanh khoản giảm trong nhịp tăng", action: "Giữ tiền mặt cao hơn." },
  { signal: "Khối ngoại bán ròng mạnh", action: "Giảm nhóm nhạy cảm với dòng vốn." },
  { signal: "USD/VND tăng nhanh", action: "Hạn chế margin." },
  { signal: "Ngân hàng suy yếu đồng loạt", action: "Hạ tỷ trọng cổ phiếu." },
  { signal: "Cổ phiếu đầu cơ tăng nóng", action: "Chốt lời từng phần, không đuổi giá." },
];

const STABLE_VN_SECTOR_NAMES = [
  "Ngân hàng",
  "Dầu khí",
  "Chứng khoán",
  "Khu công nghiệp",
  "Xuất khẩu",
  "Bất động sản",
  "Thép",
  "Bán lẻ",
];

const DEFAULT_GLOBAL_MACRO_DRIVERS_SNIPPET = [
  {
    title: "Lãi suất Mỹ còn cao",
    analysis:
      "Khi Fed chưa vội hạ lãi suất, lợi suất trái phiếu Mỹ dễ duy trì ở vùng tương đối cao. " +
      "Chi phí vốn toàn cầu đắt hơn và tài sản rủi ro khó mở rộng định giá mạnh nếu không có tin tích cực rõ ràng.",
    vietnam_impact:
      "Kênh tâm lý risk-off và dòng vốn: nhà đầu tư mới nổi thường thận trọng hơn; " +
      "cổ phiếu Việt Nam cần dựa nhiều vào dòng tiền nội.",
  },
  {
    title: "Đồng USD mạnh gây áp lực tỷ giá",
    analysis:
      "USD mạnh thường kéo chi phí nhập khẩu hàng hóa USD và làm thắt tài chính cho các DN có nợ ngoại tệ.",
    vietnam_impact: "Áp lực lên USD/VND và kỳ vọng chính sách; khối ngoại có thể cân nhắc tốc độ phân bổ.",
  },
  {
    title: "Giá dầu là rủi ro lạm phát",
    analysis:
      "Dầu cao không chỉ tác động nhóm năng lượng mà lan sang vận tải, sản xuất và kỳ vọng lạm phát.",
    vietnam_impact:
      "Biên lợi nhuận DN sử dụng năng lượng và logistics chịu áp lực; tâm lý thị trường dễ nhạy với shock giá.",
  },
];

const DEFAULT_SECTOR_PRIORITY_SNIPPET = [
  { sector: "Ngân hàng", view: "Tích cực có chọn lọc", action: "Ưu tiên mã nền tảng và room tín dụng lành mạnh." },
  { sector: "Dầu khí", view: "Tích cực ngắn hạn có điều kiện", action: "Theo giá dầu; quản trị nhịp điều chỉnh." },
  { sector: "Chứng khoán", view: "Phụ thuộc thanh khoản", action: "Chỉ mạnh khi dòng tiền cá nhân bền." },
  { sector: "Khu công nghiệp", view: "Trung tính tích cực", action: "Chọn KCN có lấp đầy và khách ổn định." },
  { sector: "Xuất khẩu", view: "Trung tính", action: "Lưu ý USD/VND và cầu bên ngoài." },
  { sector: "Bất động sản", view: "Thận trọng", action: "Chỉ xem dự án có dòng tiền và pháp lý rõ." },
  { sector: "Thép", view: "Trung tính thận trọng", action: "Bám giá nguyên liệu và biên." },
  { sector: "Bán lẻ", view: "Chọn lọc", action: "Ưu tiên chuỗi có động lực same-store." },
];

const CANONICAL_QUICK_STATES = [
  "Cầm nhiều tiền mặt",
  "Đang nắm cổ phiếu tốt",
  "Đang lãi ngắn hạn",
  "Đang dùng margin cao",
  "Muốn mua mới",
  "Đang kẹt cổ phiếu yếu",
];

const QUICK_ACTION_FALLBACKS = {
  "Cầm nhiều tiền mặt":
    "Chuẩn bị danh mục theo 3 kịch bản; chỉ giải ngân khi VN-Index, thanh khoản và độ rộng cùng xác nhận.",
  "Đang nắm cổ phiếu tốt":
    "Ưu tiên giữ mã chất lượng; tăng thêm tỷ trọng chỉ khi bứt nền kèm volume; dùng chốt lời theo lớp.",
  "Đang lãi ngắn hạn":
    "Chốt lời từng phần ở kháng cự; giữ phần cốt lõi; tránh dùng margin để kéo thêm rủi ro.",
  "Đang dùng margin cao":
    "Ưu tiên hạ đòn bẩy khi biên an toàn thu hẹp; không mua đuổi trong nhịp nhiễu hoặc thiếu xác nhận dòng tiền.",
  "Muốn mua mới":
    "Mua có kế hoạch, phân bổ theo danh mục; chờ pull-back có cấu trúc; tránh dồn tập trung một mã.",
  "Đang kẹt cổ phiếu yếu":
    "Cắt giảm dứt khoát phần yếu/thanh khoản kém; không trung bình giá xuống thác; tập trung vốn vào mã chất lượng.",
};

const JARGON_PATTERNS = [
  /\bAI\b/g,
  /\bGPT\b/g,
  /\bGemini\b/g,
  /artificial intelligence/gi,
  /\bautomation\b/gi,
  /\bcrawler\b/gi,
  /\bcrawl\b/gi,
  /\bpipeline\b/gi,
  /source quality/gi,
  /verified links/gi,
  /không phải khuyến nghị đầu tư/gi,
  /\bdisclaimer\b/gi,
  /\bmodel\b/gi,
];

const GLOBAL_KW_RE =
  /fed|mỹ|my\b|usd|dxy|lợi suất|loi suat|dầu|dau|lạm phát|lam phat|trung quốc|trung quoc|thương mại|thuong mai|địa chính trị|dia chinh tri|toàn cầu|toan cau|euro|ecb|opec|brent|thế giới|the gioi|global|china|oil|inflation|geopolit|imf/i;

const INCREASE_BAD_RE =
  /(giá )?dầu.*tăng mạnh|giá vàng.*tăng mạnh|leo thang|xấu đi|bán ròng mạnh|lạm phát.*cao hơn|lam phat.*cao hon|dự kiến.*lạm phát|du kien.*lam phat|dữ liệu lạm phát|du lieu lam phat|gián đoạn.*chuỗi|gian doan.*chuo|gián đoạn.*cung|tắc nghẽn.*cung|chuỗi cung ứng.*(gián|tắc|rủi ro)|USD\/VND tăng nhanh|thủng hỗ trợ|suy yếu đồng loạt|suy yeu dong loat|rủi ro hệ thống|căng thẳng địa chính trị/i;

const INCREASE_EXCEPTION_RE =
  /giảm bán|giam ban|ổn định|on dinh|hạ nhiệt|ha nhiet|cải thiện|co phieu khỏe/i;

const REDUCE_GOOD_RE =
  /tăng trưởng.*ổn định|tang truong.*on dinh|lạm phát thấp hơn|lam phat thap hon|ngân hàng cải thiện|ngan hang cai thien|khối ngoại mua ròng|khoi ngoai mua rong|USD\/VND ổn định|thanh khoản cải thiện|thanh khoan cai thien|đầu tư công tăng|dau tu cong tang|đầu tư công.*tốc|tăng tốc đầu tư công/i;

const DIRECT_ASSET_PITCH_RE =
  /(tăng cường\s+)?nắm giữ.*(vàng|dầu thô|vàng và dầu)|mua\s+(vàng|dầu)|khuyến nghị.*(vàng|dầu)|ưu tiên.*(vàng|dầu)(?!\s+cao)/i;

const SCENARIO_ACTION_PORTFOLIO_RE =
  /(tăng cường\s+)?nắm giữ.*(vàng|dầu|tài sản trú ẩn)|mua\s+(vàng|dầu)|tăng cường đầu tư vào\s+(cổ phiếu|hạ tầng)/i;

const LIST_MINS = { increase_risk_signals: 4, reduce_risk_signals: 4, sector_priority: 6 };

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function deepCopy(x) {
  return JSON.parse(JSON.stringify(x));
}

function stripJargonStr(s) {
  let out = s || "";
  for (const re of JARGON_PATTERNS) {
    out = out.replace(re, "");
  }
  return out.replace(/\s+/g, " ").trim();
}

function sanitizeStringsObj(obj) {
  if (typeof obj === "string") return stripJargonStr(obj);
  if (Array.isArray(obj)) return obj.map(sanitizeStringsObj);
  if (obj && typeof obj === "object") {
    const o = {};
    for (const [k, v] of Object.entries(obj)) o[k] = sanitizeStringsObj(v);
    return o;
  }
  return obj;
}

function allocationViolates(rows) {
  if (!Array.isArray(rows)) return true;
  for (const r of rows) {
    if (!r || typeof r !== "object") return true;
    const profile = String(r.profile || "").toLowerCase();
    const margin = String(r.margin || "");
    if (profile.includes("thận trọng") || profile.includes("than trong")) {
      if (/\d\s*%/.test(margin)) return true;
    }
    if (profile.includes("cân bằng") || profile.includes("can bang")) {
      if (/(?:^|[^\d])(?:10|20|30)\s*%/i.test(margin)) return true;
    }
  }
  return false;
}

function macroDriverIsGlobal(row) {
  const blob = `${row.title || ""} ${row.analysis || ""}`;
  return GLOBAL_KW_RE.test(blob);
}

function sectorStable(name) {
  const n = String(name || "").trim().toLowerCase();
  return STABLE_VN_SECTOR_NAMES.some((s) => s.toLowerCase() === n);
}

function dedupeInc(items) {
  const seen = new Set();
  const out = [];
  for (const it of items) {
    const k = (it.signal || "").trim().toLowerCase();
    if (!k || seen.has(k)) continue;
    seen.add(k);
    out.push(it);
  }
  return out;
}

function dedupeRed(items) {
  const seen = new Set();
  const out = [];
  for (const it of items) {
    const k = (it.signal || "").trim().toLowerCase();
    if (!k || seen.has(k)) continue;
    seen.add(k);
    out.push(it);
  }
  return out;
}

function sanitizeStrategyBriefSnake(snake) {
  const out = deepCopy(snake);
  const strKeys = [
    "title",
    "publication_intro",
    "main_thesis",
    "vietnam_transmission",
    "scenario_plan",
    "final_takeaway",
  ];
  for (const k of strKeys) {
    if (out[k] != null) out[k] = sanitizeStringsObj(out[k]);
  }
  for (const k of [
    "global_macro_drivers",
    "quick_actions",
    "allocation_guide",
    "sector_priority",
    "increase_risk_signals",
    "reduce_risk_signals",
  ]) {
    if (out[k] != null) out[k] = sanitizeStringsObj(out[k]);
  }

  const mt = out.main_thesis;
  if (mt && typeof mt === "object") {
    const ac = String(mt.action_conclusion || "");
    if (
      DIRECT_ASSET_PITCH_RE.test(ac) ||
      (/trú ẩn/i.test(ac) && (/vàng/i.test(ac) || /dầu/i.test(ac)))
    ) {
      mt.action_conclusion = SAFE_ACTION_CONCLUSION;
    }
  }

  if (allocationViolates(out.allocation_guide)) {
    out.allocation_guide = deepCopy(SAFE_ALLOCATION_GUIDE);
  }

  const inc = Array.isArray(out.increase_risk_signals) ? out.increase_risk_signals : [];
  const red = Array.isArray(out.reduce_risk_signals) ? out.reduce_risk_signals : [];
  const newInc = [];
  const newRed = [];

  for (const r of inc) {
    if (!r || typeof r !== "object") continue;
    const sig = String(r.signal || "").trim();
    const meaning = String(r.meaning || "").trim();
    if (!sig) continue;
    if (INCREASE_BAD_RE.test(sig) && !INCREASE_EXCEPTION_RE.test(sig)) {
      newRed.push({
        signal: sig,
        action: "Giữ kỷ luật vốn; không mua đuổi khi tín hiệu rủi ro chi phối.",
      });
    } else {
      newInc.push({ signal: sig, meaning: meaning || "—" });
    }
  }

  for (const r of red) {
    if (!r || typeof r !== "object") continue;
    const sig = String(r.signal || "").trim();
    const act = String(r.action || "").trim();
    if (!sig) continue;
    if (REDUCE_GOOD_RE.test(sig)) {
      newInc.push({
        signal: sig,
        meaning:
          "Tín hiệu xác nhận dòng tiền / vĩ mô thuận lợi hơn; có thể từng bước tăng tỷ trọng có kiểm soát.",
      });
    } else {
      let actAdj = act;
      if (
        DIRECT_ASSET_PITCH_RE.test(actAdj) ||
        (/vàng/i.test(actAdj) && (/nắm giữ/i.test(actAdj) || /mua/i.test(actAdj)))
      ) {
        actAdj = "Thận trọng; ưu tiên quản trị vốn và hạn chế đuổi giá khi biến động gia tăng.";
      }
      newRed.push({ signal: sig, action: actAdj || "Thận trọng; quan sát thêm." });
    }
  }

  let incOut = dedupeInc(newInc);
  let redOut = dedupeRed(newRed);
  if (incOut.length < LIST_MINS.increase_risk_signals) {
    for (const fb of SAFE_INCREASE_RISK_SIGNALS) {
      if (incOut.length >= 6) break;
      if (!incOut.some((x) => x.signal.toLowerCase() === fb.signal.toLowerCase())) incOut.push({ ...fb });
    }
  }
  if (redOut.length < LIST_MINS.reduce_risk_signals) {
    for (const fb of SAFE_REDUCE_RISK_SIGNALS) {
      if (redOut.length >= 6) break;
      if (!redOut.some((x) => x.signal.toLowerCase() === fb.signal.toLowerCase())) redOut.push({ ...fb });
    }
  }
  out.increase_risk_signals = incOut.slice(0, 8);
  out.reduce_risk_signals = redOut.slice(0, 8);

  const spList = out.sector_priority;
  if (Array.isArray(spList)) {
    const bad = spList.filter((r) => r && typeof r === "object" && !sectorStable(r.sector)).length;
    if (bad > 2 || spList.length < LIST_MINS.sector_priority) {
      out.sector_priority = deepCopy(DEFAULT_SECTOR_PRIORITY_SNIPPET);
    }
  }

  const gmd = out.global_macro_drivers;
  if (Array.isArray(gmd)) {
    const globalRows = gmd.filter((r) => r && typeof r === "object" && macroDriverIsGlobal(r)).map((r) => ({ ...r }));
    if (globalRows.length < 2) {
      out.global_macro_drivers = deepCopy(DEFAULT_GLOBAL_MACRO_DRIVERS_SNIPPET);
    } else {
      const merged = globalRows.slice();
      let i = 0;
      while (merged.length < 3 && i < DEFAULT_GLOBAL_MACRO_DRIVERS_SNIPPET.length) {
        const cand = DEFAULT_GLOBAL_MACRO_DRIVERS_SNIPPET[i];
        if (!merged.some((c) => String(c.title) === String(cand.title))) merged.push(deepCopy(cand));
        i++;
      }
      out.global_macro_drivers = merged.slice(0, 4);
    }
  }

  const qa = out.quick_actions;
  if (Array.isArray(qa) && qa.length) {
    const byLower = {};
    for (const r of qa) {
      if (!r || typeof r !== "object") continue;
      const st = String(r.investor_state || "").trim();
      if (st) byLower[st.toLowerCase()] = String(r.action || "").trim();
    }
    const ordered = [];
    for (const canon of CANONICAL_QUICK_STATES) {
      let act = byLower[canon.toLowerCase()] || "";
      if (!act) {
        for (const [lk, ac] of Object.entries(byLower)) {
          if (lk.includes(canon.toLowerCase().slice(0, 8)) || canon.toLowerCase().includes(lk.slice(0, 6))) {
            act = ac;
            break;
          }
        }
      }
      ordered.push({
        investor_state: canon,
        action: act || "Giữ kỷ luật vốn; chờ tín hiệu rõ trên VN-Index và thanh khoản.",
      });
    }
    const actsNonempty = ordered.map((x) => String(x.action || "").trim()).filter(Boolean);
    if (actsNonempty.length >= 4 && new Set(actsNonempty).size <= 2) {
      out.quick_actions = CANONICAL_QUICK_STATES.map((c) => ({
        investor_state: c,
        action: QUICK_ACTION_FALLBACKS[c],
      })).slice(0, 8);
    } else {
      out.quick_actions = ordered.slice(0, 8);
    }
  }

  const spPlan = out.scenario_plan;
  if (spPlan && typeof spPlan === "object") {
    const scenarioSafe = {
      base_case:
        "Giữ tỷ trọng cân bằng theo hồ sơ rủi ro; ưu tiên chất lượng và thanh khoản; hạn chế margin khi chưa có xác nhận dòng tiền.",
      bull_case:
        "Tăng dần tỷ trọng cổ phiếu trong danh mục khi độ rộng và thanh khoản xác nhận; tránh dồn quá tập trung một nhóm.",
      bear_case:
        "Hạ đòn bẩy; nâng tiền mặt; chỉ giữ cổ phiếu chất lượng cao và thanh khoản tốt.",
    };
    for (const [caseKey, safeAct] of Object.entries(scenarioSafe)) {
      const blk = spPlan[caseKey];
      if (!blk || typeof blk !== "object") continue;
      const act = String(blk.action || "").trim();
      if (SCENARIO_ACTION_PORTFOLIO_RE.test(act) || DIRECT_ASSET_PITCH_RE.test(act)) {
        blk.action = safeAct;
      }
    }
  }

  let ft = String(out.final_takeaway || "").trim();
  if (ft.length > 520) out.final_takeaway = ft.slice(0, 517).trimEnd() + "…";

  return out;
}

function camelScenario(sp) {
  const out = {};
  const pairs = [
    ["base_case", "baseCase"],
    ["bull_case", "bullCase"],
    ["bear_case", "bearCase"],
  ];
  for (const [snake, camel] of pairs) {
    const b = (sp && sp[snake]) || {};
    out[camel] = {
      title: b.title || "",
      description: b.description || "",
      action: b.action || "",
    };
  }
  return out;
}

function toPublic(snake) {
  const pub = snake.publication_intro || {};
  const mt = snake.main_thesis || {};
  const vt = snake.vietnam_transmission || {};
  const sp = snake.scenario_plan || {};
  return {
    publicationIntro: {
      headline: pub.headline || "",
      description: pub.description || "",
    },
    mainThesis: {
      regime: mt.regime || "",
      thesis: mt.thesis || "",
      actionConclusion: mt.action_conclusion || "",
    },
    globalMacroDrivers: (snake.global_macro_drivers || []).map((r) => ({
      title: r.title || "",
      analysis: r.analysis || "",
      vietnamImpact: r.vietnam_impact || "",
    })),
    vietnamTransmission: {
      summary: vt.summary || "",
      chains: Array.isArray(vt.chains) ? vt.chains : [],
    },
    quickActions: (snake.quick_actions || []).map((r) => ({
      investorState: r.investor_state || "",
      action: r.action || "",
    })),
    allocationGuide: (snake.allocation_guide || []).map((r) => ({
      profile: r.profile || "",
      stocks: r.stocks || "",
      cash: r.cash || "",
      margin: r.margin || "",
    })),
    sectorPriority: (snake.sector_priority || []).map((r) => ({
      sector: r.sector || "",
      view: r.view || "",
      action: r.action || "",
    })),
    increaseRiskSignals: (snake.increase_risk_signals || []).map((r) => ({
      signal: r.signal || "",
      meaning: r.meaning || "",
    })),
    reduceRiskSignals: (snake.reduce_risk_signals || []).map((r) => ({
      signal: r.signal || "",
      action: r.action || "",
    })),
    scenarioPlan: camelScenario(sp),
    finalTakeaway: snake.final_takeaway || "",
  };
}

function buildArticleCardsSimple(enriched, oldByUrl) {
  const articles = Array.isArray(enriched?.articles) ? [...enriched.articles] : [];
  articles.sort((a, b) => String(b.published_at || "").localeCompare(String(a.published_at || "")));
  return articles
    .filter((a) => a && a.url)
    .map((article) => {
      const prev = oldByUrl?.get(article.url);
      const summary = String(article.summary || "")
        .replace(/<[^>]+>/g, " ")
        .replace(/\s+/g, " ")
        .trim();
      return {
        title: article.title || "Tin",
        url: article.url,
        source: article.source || "",
        category: article.category || "",
        region: article.region || "",
        published_at: article.published_at || "",
        summary: summary || prev?.summary || "",
        image_url: prev?.image_url || "",
        metadata_status: prev?.metadata_status || "skipped",
      };
    });
}

function loadMarketSnapshot() {
  try {
    const p = path.join(root, "market_snapshot.json");
    const d = readJson(p);
    if (d && typeof d === "object") return d;
  } catch {
    /* ok */
  }
  return { generated_at: "", assets: [], coverage_note: "" };
}

function main() {
  const final = readJson(path.join(root, "final_summary.json"));
  const rawSummary = final.summary;
  if (!rawSummary || typeof rawSummary !== "object") {
    console.error("final_summary.json missing summary object");
    process.exit(1);
  }
  const snake = sanitizeStrategyBriefSnake(deepCopy(rawSummary));
  const generatedAt =
    String(snake.generated_at || "").trim() ||
    String(rawSummary.generated_at || "").trim() ||
    String(final.generated_at || "").trim() ||
    new Date().toISOString();

  const brief = toPublic(snake);
  let enriched = { articles: [], count: 0 };
  try {
    enriched = readJson(path.join(root, "enriched_news.json"));
  } catch {
    /* ok */
  }
  let oldByUrl = new Map();
  let oldMarketSnapshot = null;
  try {
    const oldContent = readJson(path.join(root, "content.json"));
    for (const a of oldContent.allArticles || []) {
      if (a && a.url) oldByUrl.set(a.url, a);
    }
    if (oldContent.marketSnapshot && typeof oldContent.marketSnapshot === "object") {
      oldMarketSnapshot = oldContent.marketSnapshot;
    }
  } catch {
    /* ok */
  }
  const allArticles = buildArticleCardsSimple(enriched, oldByUrl);
  const meta = typeof final.meta === "object" && final.meta ? final.meta : {};

  const fileMs = loadMarketSnapshot();
  const marketSnapshot =
    fileMs && Array.isArray(fileMs.assets) && fileMs.assets.length
      ? fileMs
      : oldMarketSnapshot || fileMs || { generated_at: "", assets: [], coverage_note: "" };

  const content = {
    siteTitle: "LEON Quant Labs",
    sectionLabel: "Góc nhìn vĩ mô và chiến lược thị trường",
    generatedAt,
    schemaVersion: "investment-strategy-brief-v1",
    publicationIntro: brief.publicationIntro,
    mainThesis: brief.mainThesis,
    globalMacroDrivers: brief.globalMacroDrivers,
    vietnamTransmission: brief.vietnamTransmission,
    quickActions: brief.quickActions,
    allocationGuide: brief.allocationGuide,
    sectorPriority: brief.sectorPriority,
    increaseRiskSignals: brief.increaseRiskSignals,
    reduceRiskSignals: brief.reduceRiskSignals,
    scenarioPlan: brief.scenarioPlan,
    finalTakeaway: brief.finalTakeaway,
    allArticles,
    stats: {
      articlesCrawled: allArticles.length,
      articlesInEnriched: enriched.count ?? enriched.articles?.length ?? 0,
    },
    editorialMeta: {
      briefDate: snake.date || "",
      briefTitle: snake.title || "",
      sourcesScanned: meta.sources_scanned,
      articlesSelected: meta.articles_selected,
      verifiedLinks: meta.verified_links,
      usedFallback: meta.used_fallback,
    },
    marketSnapshot,
  };

  fs.writeFileSync(path.join(root, "content.json"), JSON.stringify(content, null, 2), "utf8");
  console.log("Wrote content.json with", allArticles.length, "articles (brief sanitized in-memory).");
}

main();
