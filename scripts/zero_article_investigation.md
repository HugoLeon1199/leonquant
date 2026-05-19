# Dieu tra nguon 0 bai trong DB

Tong seed: 99

Nguon **0 bai DB**: 37

## Chi NotToday (crawl OK, sai ngay) — khong sua code (6)

- **bls.gov** | `rss_then_article_extract` | skip=False | Crawl duoc; 0 bai vi loc ngay (NotToday) — KHONG phai loi code | loi: NotToday:5
- **ecb.europa.eu** | `sitemap_then_article_extract` | skip=False | Crawl duoc; 0 bai vi loc ngay (NotToday) — KHONG phai loi code | loi: NotToday:250
- **enternews.vn** | `rss_then_article_extract` | skip=True | Crawl duoc; 0 bai vi loc ngay (NotToday) — KHONG phai loi code | loi: NotToday:60
- **home.treasury.gov** | `rss_then_article_extract` | skip=False | Crawl duoc; 0 bai vi loc ngay (NotToday) — KHONG phai loi code | loi: NotToday:50
- **kitco.com** | `sitemap_then_article_extract` | skip=False | Crawl duoc; 0 bai vi loc ngay (NotToday) — KHONG phai loi code | loi: NotToday:250
- **vccinews.vn** | `sitemap_then_article_extract` | skip=False | Crawl duoc; 0 bai vi loc ngay (NotToday) — KHONG phai loi code | loi: NotToday:60

## Chu yeu NotToday (1)

- **bis.org** | `sitemap_then_article_extract` | skip=False | Chu yeu NotToday (22); co the co bai ngay khac | loi: ShortContent:228, NotToday:22

## Can Playwright (bo qua theo yeu cau) (7)

- **customs.gov.vn** | `playwright_fallback` | skip=False | Profiler chon Playwright; Scrapy khong render JS | loi: ShortContent:7
- **hsx.vn** | `playwright_fallback` | skip=False | Profiler chon Playwright; Scrapy khong render JS | loi: ShortContent:7
- **kinhtechungkhoan.vn** | `playwright_fallback` | skip=True | Profiler chon Playwright; Scrapy khong render JS | loi: HttpError:8
- **laodong.vn** | `playwright_fallback` | skip=False | Profiler chon Playwright; Scrapy khong render JS | loi: ShortContent:8
- **mof.gov.vn** | `playwright_fallback` | skip=False | Profiler chon Playwright; Scrapy khong render JS | loi: ShortContent:7
- **nguoiquansat.vn** | `playwright_fallback` | skip=True | Profiler chon Playwright; Scrapy khong render JS | loi: HttpError:8
- **thitruongtaichinhtiente.vn** | `playwright_fallback` | skip=True | Profiler chon Playwright; Scrapy khong render JS | loi: HttpError:8

## Profile loi (10)

- **baotintuc.vn** | `manual_review` | skip=True | Profile loi — chua lane Scrapy on dinh | loi: ConnectTimeout:2
- **bnews.vn** | `manual_review` | skip=True | Profile loi — chua lane Scrapy on dinh | loi: ConnectError:3
- **diaoconline.vn** | `manual_review` | skip=True | Profile loi — chua lane Scrapy on dinh | loi: ConnectTimeout:2
- **gso.gov.vn** | `manual_review` | skip=True | Profile loi — chua lane Scrapy on dinh | loi: ConnectTimeout:2
- **hnx.vn** | `manual_review` | skip=True | Profile loi — chua lane Scrapy on dinh | loi: ConnectError:3
- **kinhtedothi.vn** | `manual_review` | skip=True | Profile loi — chua lane Scrapy on dinh | loi: ConnectTimeout:2
- **mard.gov.vn** | `manual_review` | skip=True | Profile loi — chua lane Scrapy on dinh | loi: ConnectError:2, ConnectTimeout:1
- **monre.gov.vn** | `manual_review` | skip=True | Profile loi — chua lane Scrapy on dinh | loi: ConnectError:3
- **mpi.gov.vn** | `manual_review` | skip=True | Profile loi — chua lane Scrapy on dinh | loi: ConnectError:3
- **xaydung.gov.vn** | `manual_review` | skip=True | Profile loi — chua lane Scrapy on dinh | loi: ConnectError:3

## Chan that (HTTP/SSL) (4)

- **bea.gov** | `rss_then_article_extract` | skip=True | Tren skip list (HTTP/SSL that) | loi: FetchError:7
- **reuters.com** | `sitemap_then_article_extract` | skip=True | Tren skip list (HTTP/SSL that) | loi: FetchError:260
- **taichinhdoanhnghiep.net.vn** | `rss_then_article_extract` | skip=True | Tren skip list (HTTP/SSL that) | loi: FetchError:8
- **thedefiant.io** | `rss_then_article_extract` | skip=True | Tren skip list (HTTP/SSL that) | loi: FetchError:7

## AccessControl (die tra heuristic) (5)

- **apnews.com** | `sitemap_then_article_extract` | skip=False | AccessControl con 215 — xem lai extract/HTML (sau fix nen giam) | loi: AccessControlDetected:215
- **thesaigontimes.vn** | `sitemap_then_article_extract` | skip=False | AccessControl con 300 — xem lai extract/HTML (sau fix nen giam) | loi: AccessControlDetected:300
- **thuongtruong.com.vn** | `sitemap_then_article_extract` | skip=False | AccessControl con 24 — xem lai extract/HTML (sau fix nen giam) | loi: NotToday:126, AccessControlDetected:24
- **vietstock.vn** | `sitemap_then_article_extract` | skip=False | AccessControl con 295 — xem lai extract/HTML (sau fix nen giam) | loi: AccessControlDetected:295
- **vov.vn** | `sitemap_then_article_extract` | skip=False | AccessControl con 250 — xem lai extract/HTML (sau fix nen giam) | loi: AccessControlDetected:250

## Chua thay log crawl (2)

- **nhadatvui.vn** | `sitemap_then_article_extract` | skip=False | Khong co crawl_errors — co the chua vao tier / chua chay toi
- **qdnd.vn** | `sitemap_then_article_extract` | skip=False | Khong co crawl_errors — co the chua vao tier / chua chay toi

## Loi mang mot phan (1)

- **eia.gov** | `sitemap_then_article_extract` | skip=False | [('NotToday', 225), ('FetchError', 15), ('HttpError', 5)] | loi: NotToday:225, FetchError:15, HttpError:5

## Khac (1)

- **ssc.gov.vn** | `html_then_trafilatura` | skip=False | ReadTimeout:2 | loi: ReadTimeout:2

## Rui ro trong code (can xem)

- `playwright_fallback` -> RSS/sitemap/HTML Scrapy, khong Playwright
- RSS 404 (vd dantri feed path) -> 0 URL enqueue
- `today_only` + cap 50 link moi nhat -> nhieu NotToday
- Listing URL vao DB neu extract du dai (tieu de 'trang 1')
