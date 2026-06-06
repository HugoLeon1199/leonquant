# API news source quality tests (standalone)

Module đánh giá **đầu vào** từ 3 API tin tức — **không** tích hợp web, **không** sửa pipeline Tin48h / Invest / LIVE.

## APIs

| API | Env var |
|-----|---------|
| [NewsData.io](https://newsdata.io/) | `NEWSDATA_API_KEY` |
| [GNews.io](https://gnews.io/) | `GNEWS_API_KEY` |
| [WorldNews API](https://worldnewsapi.com/) | `WORLDNEWS_API_KEY` |

Key API nằm trong `.env.example` (CI đọc file này). Local có thể override trong `.env` (gitignore).

## Chạy

```bash
python api_tests/test_news_apis.py
```

Từ thư mục gốc `leonquant/`.

## Cron 30 phút (1 request / lần)

Luân phiên **worldnews → gnews → newsdata**, gom URL unique vào `data/`:

```bash
python api_tests/cron_fetch.py
```

GitHub Actions: `.github/workflows/api-cron-30m.yml` (`*/30 * * * *` UTC), bot commit `api_tests/data/cron_accumulator.json` + `cron_summary.md`.

Mai xem tổng trong `api_tests/data/cron_summary.md`.

## Output

| File | Mô tả |
|------|--------|
| `output/newsdata_sample.json` | Bài chuẩn hóa + meta response |
| `output/gnews_sample.json` | |
| `output/worldnews_sample.json` | |
| `output/api_quality_report.md` | Báo cáo so sánh + khuyến nghị |
| `output/api_quality_report.csv` | Từng bài để lọc nhanh |

Query chung: `economy OR finance OR market`, English, cửa sổ ~48h (theo khả năng từng API), ~30 bài/API.

## So sánh trùng nguồn

Script đọc URL từ `content.json` (nếu có) để ước lượng overlap với pipeline crawl hiện tại — chỉ đọc, không ghi.
