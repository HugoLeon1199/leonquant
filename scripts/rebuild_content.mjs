/**
 * Wrapper: dựng content.json qua build_website_content.py (Global Market Strategy Brief v2).
 * Luôn ưu tiên Python để tránh lệch logic với sanitize/coerce trong repo.
 *
 * Usage: node scripts/rebuild_content.mjs [--with-images]
 */
import { spawnSync } from "node:child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");

function main() {
  const argv = process.argv.slice(2);
  const withImages = argv.includes("--with-images");
  const pyArgs = ["build_website_content.py"];
  if (!withImages) pyArgs.push("--skip-images");

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
      return;
    }
  }

  console.error("Không chạy được build_website_content.py. Cài Python 3 và thử:");
  console.error(`  cd ${root}`);
  console.error(`  python build_website_content.py --skip-images`);
  process.exit(1);
}

main();
