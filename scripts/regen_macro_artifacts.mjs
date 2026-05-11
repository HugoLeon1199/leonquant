/**
 * Đồng bộ sample brief + content.json khi không muốn chạy tay từng bước.
 * Gọi inject preview (schema Investment Strategy Brief) rồi build_website_content.
 */
import { execSync } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");

function run(cmd) {
  execSync(cmd, { cwd: root, stdio: "inherit", shell: true });
}

function main() {
  run("python scripts/inject_preview_brief.py");
  run("python build_website_content.py --skip-images");
}

main();
