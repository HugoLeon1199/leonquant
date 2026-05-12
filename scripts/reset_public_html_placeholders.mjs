/**
 * Khôi phục brief + sourceGrid placeholders rỗng trong landing_page.html (sau khi chạy embed cục bộ).
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const p = path.join(root, "landing_page.html");

let s = fs.readFileSync(p, "utf8");
const mainStart = s.indexOf("  <main>");
const mainEnd = s.lastIndexOf("  </main>") + 9;
const skeleton = `  <main>
    <section id="brief" class="alt">
      <div class="container">
        <p id="syncNote" class="sync-note"></p>
        <div id="sectionThesis" class="brief-block"></div>
        <div id="sectionMacro" class="brief-block"></div>
        <div id="sectionTransmission" class="brief-block"></div>
        <div id="sectionActions" class="brief-block"></div>
        <div id="sectionAllocation" class="brief-block"></div>
        <div id="sectionSectors" class="brief-block"></div>
        <div id="sectionRiskOn" class="brief-block"></div>
        <div id="sectionRiskOff" class="brief-block"></div>
        <div id="sectionScenarios" class="brief-block"></div>
        <div id="sectionTakeaway" class="brief-block"></div>
      </div>
    </section>

    <section id="reference" class="reference-secondary">
      <div class="container" style="max-width: min(1180px, 95%);">
        <div class="section-head secondary-head">
          <p class="eyebrow">Tham khảo</p>
          <h2 id="sourceGridTitle">Tin nền tham khảo</h2>
          <p>Danh mục tin nền được chọn lọc trong ngày — dùng để đối chiếu ngữ cảnh, không phải trọng tâm brief.</p>
        </div>
        <div id="sourceGrid" class="source-grid"></div>
      </div>
    </section>
  </main>`;

if (mainStart < 0 || mainEnd < 8) {
  console.error("Could not find <main> block");
  process.exit(1);
}
s = s.slice(0, mainStart) + skeleton + s.slice(mainEnd);
fs.writeFileSync(p, s, "utf8");
console.log("Reset placeholders in", p);
