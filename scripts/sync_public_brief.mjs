/**
 * Đồng bộ scripts/strategy_brief_seed_summary.json → final_summary.json rồi dựng content.json
 * qua build_website_content.py (Global Market Strategy Brief v2).
 */
import fs from "fs";
import path from "path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");

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

  const pyArgs = ["build_website_content.py", "--skip-images"];
  const attempts =
    process.platform === "win32"
      ? [
          { cmd: "py", args: ["-3", ...pyArgs] },
          { cmd: "python", args: pyArgs },
          { cmd: "python3", args: pyArgs },
        ]
      : [
          { cmd: "python3", args: pyArgs },
          { cmd: "python", args: pyArgs },
        ];

  for (const { cmd, args } of attempts) {
    const r = spawnSync(cmd, args, { cwd: root, stdio: "inherit" });
    if (r.status === 0) {
      console.log("Wrote", finalPath, "+ content.json via build_website_content.py");
      return;
    }
  }

  console.error("Đã cập nhật final_summary.json nhưng build_website_content.py không chạy được.");
  process.exit(1);
}

main();
