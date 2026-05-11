# LEON Quant — Daily macro brief

**Repo:** [github.com/HugoLeon1199/leonquant](https://github.com/HugoLeon1199/leonquant)

## Xem bản tin trên web (GitHub Pages)

Sau khi bật Pages (một lần), URL mặc định:

`https://hugoleon1199.github.io/leonquant/`

### Cách bật (khuyến nghị: GitHub Actions)

1. Vào repo → **Settings** → **Pages**.
2. **Build and deployment** → **Source** → chọn **GitHub Actions** (không phải “Deploy from branch” nếu bạn dùng workflow `pages.yml`).
3. Lưu. Workflow **Deploy GitHub Pages** sẽ chạy khi push `main` (hoặc chạy tay tab **Actions**).
4. Vài phút sau, mở lại URL trên.

### Cách bật thay thế (Deploy từ branch)

1. **Settings** → **Pages** → Source: **Deploy from branch**.
2. Branch: **main**, folder: **/ (root)**.
3. File `.nojekyll` ở root giúp GitHub không chạy Jekyll sai trên file HTML tĩnh.

> Repo **private** có thể không có Pages miễn phí; khi đó cần public repo hoặc gói có Pages cho private.

## Chạy pipeline local

Xem `CRAWLER_README.md`, `GPT_SUMMARY_README.md`. Build web: `python build_website_content.py`.
