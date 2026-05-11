/**
 * Áp schema Macro Intelligence vào final_summary.json và đồng bộ content.json
 * (dùng khi chưa có python / hoặc sau finalize_summary_gpt.py --skip-web-verify).
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const seedPath = path.join(__dirname, "macro_intelligence_seed.json");

const MACRO_INTELLIGENCE_SUMMARY_KEYS = new Set([
  "title",
  "date",
  "generated_at",
  "market_regime",
  "daily_thesis",
  "thirty_second_summary",
  "what_changed",
  "top_macro_drivers",
  "asset_impact_heatmap",
  "vietnam_investor_lens",
  "scenario_map",
  "key_variables_to_watch",
  "source_quality",
  "final_takeaway",
  "disclaimer",
]);

function stripSummaryToMacroSchema(s) {
  for (const k of Object.keys(s)) {
    if (!MACRO_INTELLIGENCE_SUMMARY_KEYS.has(k)) delete s[k];
  }
}

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function main() {
  const finalPath = path.join(root, "final_summary.json");
  const contentPath = path.join(root, "content.json");
  const enrichedPath = path.join(root, "enriched_news.json");

  const seed = readJson(seedPath);
  const data = readJson(finalPath);
  const enriched = fs.existsSync(enrichedPath) ? readJson(enrichedPath) : { count: 0, articles: [] };
  const content = readJson(contentPath);

  const s = data.summary;
  if (typeof s !== "object" || !s) {
    throw new Error("final_summary.json missing summary");
  }

  const now = new Date().toISOString();
  const day = now.slice(0, 10);
  const total = enriched.count ?? enriched.articles?.length ?? 0;
  const selected = Math.min(18, total || 0);

  Object.assign(s, seed);
  s.date = day;
  s.generated_at = now;

  s.source_quality = {
    sources_scanned: total,
    articles_selected: selected,
    verified_links: 0,
    coverage_note:
      "Đồng bộ từ seed + enriched_news (không live-verify). Chạy finalize_summary_gpt.py với OPENAI_API_KEY để có bản GPT đầy đủ.",
  };

  data.generated_at = now;
  data.meta = {
    ...(typeof data.meta === "object" ? data.meta : {}),
    macro_intelligence_seed: "scripts/macro_intelligence_seed.json",
    regenerated_at: now,
  };

  stripSummaryToMacroSchema(s);

  fs.writeFileSync(finalPath, JSON.stringify(data, null, 2), "utf8");
  console.log("Wrote", finalPath);

  const preservedArticles = Array.isArray(content.allArticles) ? content.allArticles : [];
  const regimeLine =
    typeof s.market_regime === "object" && s.market_regime
      ? String(s.market_regime.regime || "").trim()
      : "";

  Object.assign(content, {
    siteTitle: "LEON Quant Labs",
    sectionLabel: "Daily Macro Intelligence for Serious Investors",
    generatedAt: s.generated_at || now,
    briefDate: s.date || day,
    chatSectionTitle: s.title,
    marketImpact: regimeLine || "Mixed",
    executiveSummary: "",
    thirtySecondSummary: s.thirty_second_summary || "",
    briefStories: [],
    assetImpactTable: [],
    macroWorld: "",
    vietnamMacro: "",
    macroGlobal: "",
    internationalMarkets: "",
    vietnamImplications: "",
    soWhatChain: "",
    worldToVietnam: "",
    assetImpacts: Array.isArray(content.assetImpacts) ? content.assetImpacts : [],
    actualVsForecast: Array.isArray(content.actualVsForecast) ? content.actualVsForecast : [],
    macroHeatLabels: Array.isArray(content.macroHeatLabels) ? content.macroHeatLabels : [],
    webVerification: typeof content.webVerification === "object" && content.webVerification ? content.webVerification : {},
    risksToWatch: Array.isArray(content.risksToWatch) ? content.risksToWatch : [],
    marketRegime: s.market_regime || {},
    dailyThesis: s.daily_thesis || "",
    whatChanged: s.what_changed || "",
    topMacroDrivers: Array.isArray(s.top_macro_drivers) ? s.top_macro_drivers : [],
    assetImpactHeatmap: Array.isArray(s.asset_impact_heatmap) ? s.asset_impact_heatmap : [],
    vietnamInvestorLens: typeof s.vietnam_investor_lens === "object" ? s.vietnam_investor_lens : {},
    scenarioMap: typeof s.scenario_map === "object" ? s.scenario_map : {},
    keyVariablesToWatch: Array.isArray(s.key_variables_to_watch) ? s.key_variables_to_watch : [],
    sourceQuality: typeof s.source_quality === "object" ? s.source_quality : {},
    finalTakeaway: s.final_takeaway || "",
    disclaimer: s.disclaimer || "",
    schemaVersion: "macro-intelligence-v1",
    legacyProBrief: false,
    chatItems: [
      {
        title: s.title,
        content: [s.daily_thesis, s.what_changed, s.final_takeaway, regimeLine ? `Market regime: ${regimeLine}` : ""]
          .filter((x) => x && String(x).trim())
          .join("\n\n"),
      },
    ],
    allArticles: preservedArticles,
    featuredArticles: preservedArticles,
    stats: {
      ...(typeof content.stats === "object" ? content.stats : {}),
      articlesCrawled: preservedArticles.length,
      articlesInEnriched: total,
      pipeline: "Crawl → Gemini → GPT / seed (Macro Intelligence) → content.json",
    },
  });

  fs.writeFileSync(contentPath, JSON.stringify(content, null, 2), "utf8");
  console.log("Wrote", contentPath);
}

main();
