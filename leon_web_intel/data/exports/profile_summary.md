# Profile Summary

- total_sources: 39
- active_sources: 36
- active_candidate_sources: 3
- review_sources: 0
- error_sources: 0

## Strategy Breakdown

- api_first: 0
- rss_then_article_extract: 26
- sitemap_then_article_extract: 10
- html_then_trafilatura: 2
- playwright_fallback: 1
- metadata_only: 0
- manual_review: 0

## Readiness

Top 20 ready sources:

source_id | domain | best_strategy | rss | sitemap | html_ok
--- | --- | --- | --- | --- | ---
aljazeera_com | aljazeera.com | rss_then_article_extract | True | True | True
asia_nikkei_com | asia.nikkei.com | sitemap_then_article_extract | False | True | True
baochinhphu_vn | baochinhphu.vn | rss_then_article_extract | True | False | True
baoxaydung_vn | baoxaydung.vn | rss_then_article_extract | True | True | True
cafef_vn | cafef.vn | rss_then_article_extract | True | True | True
cnbc_com | cnbc.com | sitemap_then_article_extract | False | True | True
coindesk_com | coindesk.com | sitemap_then_article_extract | False | True | True
coingecko_com | coingecko.com | rss_then_article_extract | True | True | True
cointelegraph_com | cointelegraph.com | rss_then_article_extract | True | True | True
cryptoslate_com | cryptoslate.com | rss_then_article_extract | True | True | True
csmonitor_com | csmonitor.com | sitemap_then_article_extract | False | True | True
dantri_com_vn | dantri.com.vn | rss_then_article_extract | True | True | True
decrypt_co | decrypt.co | rss_then_article_extract | True | True | True
engadget_com | engadget.com | rss_then_article_extract | True | True | True
genk_vn | genk.vn | rss_then_article_extract | True | True | True
imf_org | imf.org | html_then_trafilatura | False | False | True
khoahoc_tv | khoahoc.tv | html_then_trafilatura | False | False | True
laodong_vn | laodong.vn | playwright_fallback | False | False | False
livescience_com | livescience.com | rss_then_article_extract | True | True | True
oilprice_com | oilprice.com | rss_then_article_extract | True | True | True

## Sources Needing Review

source_id | domain | reason | error_message
--- | --- | --- | ---
plo_vn | plo.vn | sitemap_then_article_extract | 

## Next Steps

- crawl sample active sources
- review metadata_only
- add API adapters for top official sources
- expand sources after v1 stable
