/**
 * Đồng bộ final_summary.summary (seed) → content.json (camelCase) khi chưa chạy Python.
 * Giữ nguyên allArticles + marketSnapshot từ content.json cũ.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");

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

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function main() {
  const seedPath = path.join(__dirname, "strategy_brief_seed_summary.json");
  const seedSummary = readJson(seedPath);

  const finalPath = path.join(root, "final_summary.json");
  const final = readJson(finalPath);
  const now = new Date().toISOString();
  seedSummary.date = seedSummary.date || now.slice(0, 10);
  seedSummary.generated_at = seedSummary.generated_at || now;

  final.summary = seedSummary;
  final.generated_at = now;
  final.meta = {
    ...(typeof final.meta === "object" && final.meta ? final.meta : {}),
    sync_public_brief_at: now,
  };
  fs.writeFileSync(finalPath, JSON.stringify(final, null, 2), "utf8");

  const contentPath = path.join(root, "content.json");
  const oldContent = readJson(contentPath);
  const brief = toPublic(seedSummary);

  let enrichedCount = 0;
  try {
    const en = readJson(path.join(root, "enriched_news.json"));
    enrichedCount = en.count ?? en.articles?.length ?? 0;
  } catch {
    /* ok */
  }

  const articles = Array.isArray(oldContent.allArticles) ? oldContent.allArticles : [];

  const newContent = {
    siteTitle: "LEON Quant Labs",
    sectionLabel: "Góc nhìn vĩ mô và chiến lược thị trường",
    generatedAt: seedSummary.generated_at,
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
    allArticles: articles,
    stats: {
      articlesCrawled: articles.length,
      articlesInEnriched: enrichedCount,
    },
    editorialMeta: {
      briefDate: seedSummary.date,
      briefTitle: seedSummary.title,
    },
    marketSnapshot:
      oldContent.marketSnapshot && typeof oldContent.marketSnapshot === "object"
        ? oldContent.marketSnapshot
        : { generated_at: "", assets: [], coverage_note: "" },
  };

  fs.writeFileSync(contentPath, JSON.stringify(newContent, null, 2), "utf8");
  console.log("Wrote", finalPath);
  console.log("Wrote", contentPath);
}

main();
