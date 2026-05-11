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
  s.executive_summary = "";
  s.brief_stories = [];
  s.asset_impact_table = [];

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

  fs.writeFileSync(finalPath, JSON.stringify(data, null, 2), "utf8");
  console.log("Wrote", finalPath);

  const heatRows = [];
  for (const row of s.asset_impact_heatmap || []) {
    if (!row || typeof row !== "object") continue;
    heatRows.push({
      group: row.asset || "—",
      impact_today: `${row.direction || ""} · ${row.strength || ""}`.replace(/^ ·|· $/g, "").trim(),
      main_reason: row.main_reason || "",
    });
  }

  Object.assign(content, {
    siteTitle: "LEON Quant Labs",
    sectionLabel: "Daily Macro Intelligence for Serious Investors",
    generatedAt: s.generated_at || now,
    briefDate: s.date || day,
    chatSectionTitle: s.title,
    marketImpact: s.market_impact || "Mixed",
    executiveSummary: s.executive_summary || "",
    thirtySecondSummary: s.thirty_second_summary || "",
    briefStories: [],
    assetImpactTable: heatRows,
    macroWorld: s.macro_world || "",
    vietnamMacro: s.vietnam_macro || "",
    macroGlobal: s.macro_global || "",
    internationalMarkets: s.international_markets || "",
    vietnamImplications: s.vietnam_implications || "",
    soWhatChain: s.so_what_chain || "",
    worldToVietnam: s.world_to_vietnam || "",
    assetImpacts: Array.isArray(s.asset_impacts) ? s.asset_impacts : content.assetImpacts || [],
    actualVsForecast: Array.isArray(s.actual_vs_forecast) ? s.actual_vs_forecast : content.actualVsForecast || [],
    macroHeatLabels: Array.isArray(s.macro_heat_labels) ? s.macro_heat_labels : content.macroHeatLabels || [],
    webVerification: typeof s.web_verification === "object" && s.web_verification ? s.web_verification : {},
    risksToWatch: Array.isArray(s.risks_to_watch) ? s.risks_to_watch : content.risksToWatch || [],
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
        content: [s.daily_thesis, s.macro_world, s.vietnam_macro, s.what_changed]
          .filter((x) => x && String(x).trim())
          .join("\n\n"),
      },
    ],
  });

  fs.writeFileSync(contentPath, JSON.stringify(content, null, 2), "utf8");
  console.log("Wrote", contentPath);
}

main();
