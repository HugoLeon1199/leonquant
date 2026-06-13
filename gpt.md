# GPT Notes

## Repo nay lam gi

`leonquant` la repo cho web tin tuc kinh te/thi truong cua LeonQuant.

Pipeline chinh:
- Crawl tin tu nhieu nguon vao DuckDB: `scripts/run_intel_full_daily.py` + `leon_web_intel/`
- Loc/xuat du lieu cho AI: `scripts/export_news_full_for_ai.py` -> `news_for_ai.json` -> `news_for_ai_clean.json`
- Tao ban tin 48h bang Gemini: `scripts/run_digest_from_db.py`, `scripts/run_digest_loop.py`, `summarize_news_gemini.py`
- Dung du lieu web cong khai: `build_website_content.py` -> `content.json` -> `landing_page.html`
- Tab the gioi/invest dung GDELT: `leon.py`, `invest_world_pulse.json`, `market_pulse.json`

Output quan trong:
- `content.json`: du lieu web public
- `landing_page.html`: HTML trang chinh
- `gemini_digest_summary.json`: tom tat Tin48h
- `invest_vn_brief.json`: khoi Viet Nam cho tab dau tu
- `data/web_intel_leonquant.duckdb.gz`: seed DB nho de GitHub Actions bootstrap

Rule editorial Tin48h:
- Uu tien `editorial-first, source-backed second`
- Than bai tom tat/nganh viet nhu briefing, khong chen link vao giua doan
- Giu nguyen link nguon va dat cuoi tung khoi lon (`Tong quan 48h`, moi nganh)

## GitHub Actions

Workflow chinh:
- `.github/workflows/daily.yml`: crawl Tin48h + Gemini + build web + invest-world
- `.github/workflows/pages.yml`: deploy GitHub Pages

Van de da gap:
- Workflow `Tin Viet Nam 48h digest` bi fail o step `Prepare digest export window`
- Crawl step pass, nhung gate ket luan khong du bai hop le 48h de chay Gemini

## Ban da sua gi

Fix da push len remote:
- Commit `d9c1f3c` - `Harden Tin48h gate recovery on Actions`

Noi dung fix:
- Sua `scripts/prepare_digest_db.py`
- Them check `latest_extracted_at` de nhan ra truong hop DB stale/missing sau crawl
- Neu DB chua co crawl moi that su, script tra ve huong retry/recovery thay vi fail ngay

- Sua `.github/workflows/daily.yml`
- Neu gate fail, workflow se tu recovery ngay tren GitHub:
- rebuild DB tu seed profiles
- `--fresh-db`
- `--force-refresh-profile`
- recrawl
- gate lai truoc khi chay Gemini

Muc tieu:
- De workflow Tin48h tu chua lan dau tien khi cache/profile tren Actions bi hong hoac qua cu
- Giam viec phai chay local de cuu pipeline

## Trang thai gan nhat

Lan cuoi minh kiem tra:
- Run `Tin Viet Nam 48h digest`: `27427612026`
- Link: https://github.com/HugoLeon1199/leonquant/actions/runs/27427612026
- Status luc do: `in_progress`

Ghi chu:
- `invest-world` da pass
- `build-digest` dang chay o step gate/recovery lau hon truoc, cho thay fix dang co tac dung

## Cach nho nhanh cho lan sau

Neu Tin48h hong:
1. Xem run moi nhat cua `Tin Viet Nam 48h digest`
2. Kiem tra no fail o `gate`, `Gemini`, hay `commit`
3. Neu fail o gate, uu tien xem `scripts/prepare_digest_db.py` va block recovery trong `daily.yml`
4. Khong can chay local neu muc tieu la cuu pipeline GitHub
