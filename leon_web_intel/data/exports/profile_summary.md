# Profile Summary

- total_sources: 99
- active_sources: 68
- active_candidate_sources: 21
- review_sources: 10
- error_sources: 99

## Strategy Breakdown

- api_first: 0
- rss_then_article_extract: 33
- sitemap_then_article_extract: 35
- html_then_trafilatura: 12
- playwright_fallback: 9
- metadata_only: 0
- manual_review: 10

## Readiness

Top 20 ready sources:

source_id | domain | best_strategy | rss | sitemap | html_ok
--- | --- | --- | --- | --- | ---
apnews_com | apnews.com | sitemap_then_article_extract | False | True | True
asia_nikkei_com | asia.nikkei.com | sitemap_then_article_extract | False | True | True
baochinhphu_vn | baochinhphu.vn | rss_then_article_extract | True | False | True
baodautu_vn | baodautu.vn | sitemap_then_article_extract | False | True | True
baophapluat_vn | baophapluat.vn | sitemap_then_article_extract | False | True | True
baotintuc_vn | baotintuc.vn | manual_review | False | False | False
baoxaydung_vn | baoxaydung.vn | rss_then_article_extract | True | True | True
batdongsan_com_vn | batdongsan.com.vn | playwright_fallback | False | False | False
batdongsan_vn | batdongsan.vn | sitemap_then_article_extract | False | True | True
bea_gov | bea.gov | rss_then_article_extract | True | True | True
beincrypto_com | beincrypto.com | rss_then_article_extract | True | False | False
bis_org | bis.org | sitemap_then_article_extract | False | True | True
bls_gov | bls.gov | rss_then_article_extract | True | True | True
bnews_vn | bnews.vn | manual_review | False | False | False
boj_or_jp | boj.or.jp | html_then_trafilatura | False | False | True
cafebiz_vn | cafebiz.vn | rss_then_article_extract | True | True | True
cafef_vn | cafef.vn | rss_then_article_extract | True | True | True
cafeland_vn | cafeland.vn | sitemap_then_article_extract | False | True | True
chinhphu_vn | chinhphu.vn | html_then_trafilatura | False | False | True
coingecko_com | coingecko.com | html_then_trafilatura | False | False | True

## Sources Needing Review

source_id | domain | reason | error_message
--- | --- | --- | ---
apnews_com | apnews.com | sitemap_then_article_extract, paywall_signal, login_signal, captcha_signal | 
asia_nikkei_com | asia.nikkei.com | sitemap_then_article_extract, paywall_signal, login_signal | 
baochinhphu_vn | baochinhphu.vn | rss_then_article_extract, paywall_signal, login_signal, captcha_signal | 
baodautu_vn | baodautu.vn | sitemap_then_article_extract, paywall_signal, captcha_signal | 
baophapluat_vn | baophapluat.vn | sitemap_then_article_extract | 
baotintuc_vn | baotintuc.vn | manual_review | [WinError 10060] A connection attempt failed because the connected party did not properly respond after a period of time, or established connection failed because connected host has failed to respond 
baoxaydung_vn | baoxaydung.vn | rss_then_article_extract, login_signal | 
batdongsan_com_vn | batdongsan.com.vn | playwright_fallback, paywall_signal | 
batdongsan_vn | batdongsan.vn | sitemap_then_article_extract, paywall_signal | 
bea_gov | bea.gov | rss_then_article_extract, paywall_signal | 
beincrypto_com | beincrypto.com | rss_then_article_extract, paywall_signal | 
bis_org | bis.org | sitemap_then_article_extract, login_signal | 
bls_gov | bls.gov | rss_then_article_extract, paywall_signal | 
bnews_vn | bnews.vn | manual_review | [SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1000) Traceback (most recent call last):   File "C:\Users\lehoa\AppData\Roaming\Python\Python312\site-packages\
boj_or_jp | boj.or.jp | html_then_trafilatura | 
cafebiz_vn | cafebiz.vn | rss_then_article_extract, login_signal | 
cafef_vn | cafef.vn | rss_then_article_extract | 
cafeland_vn | cafeland.vn | sitemap_then_article_extract, paywall_signal | 
chinhphu_vn | chinhphu.vn | html_then_trafilatura | 
coingecko_com | coingecko.com | html_then_trafilatura, paywall_signal, login_signal, captcha_signal | 
cointelegraph_com | cointelegraph.com | rss_then_article_extract | 
congthuong_vn | congthuong.vn | sitemap_then_article_extract, paywall_signal, login_signal | 
cophieu68_vn | cophieu68.vn | html_then_trafilatura, login_signal | 
cryptoslate_com | cryptoslate.com | rss_then_article_extract, paywall_signal | 
customs_gov_vn | customs.gov.vn | playwright_fallback | 
dantri_com_vn | dantri.com.vn | rss_then_article_extract, paywall_signal, captcha_signal | 
decrypt_co | decrypt.co | rss_then_article_extract, paywall_signal, login_signal, captcha_signal | 
diaoconline_vn | diaoconline.vn | manual_review | [WinError 10060] A connection attempt failed because the connected party did not properly respond after a period of time, or established connection failed because connected host has failed to respond 
diendandoanhnghiep_vn | diendandoanhnghiep.vn | sitemap_then_article_extract | 
doanhnghiephoinhap_vn | doanhnghiephoinhap.vn | rss_then_article_extract, paywall_signal | 
doanhnhansaigon_vn | doanhnhansaigon.vn | sitemap_then_article_extract, paywall_signal | 
ecb_europa_eu | ecb.europa.eu | sitemap_then_article_extract, paywall_signal | 
eia_gov | eia.gov | sitemap_then_article_extract, paywall_signal | 
enternews_vn | enternews.vn | rss_then_article_extract | 
federalreserve_gov | federalreserve.gov | html_then_trafilatura, paywall_signal | 
forexfactory_com | forexfactory.com | playwright_fallback, paywall_signal | 
fred_stlouisfed_org | fred.stlouisfed.org | html_then_trafilatura, paywall_signal | 
fxstreet_com | fxstreet.com | rss_then_article_extract, paywall_signal, login_signal | 
gold_org | gold.org | rss_then_article_extract, paywall_signal, login_signal, captcha_signal | 
gso_gov_vn | gso.gov.vn | manual_review | [WinError 10060] A connection attempt failed because the connected party did not properly respond after a period of time, or established connection failed because connected host has failed to respond 
hnx_vn | hnx.vn | manual_review | [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1000) Traceback (most recent call last):   File "C:\Users\lehoa\AppData\Roaming\Python\Python
home_treasury_gov | home.treasury.gov | rss_then_article_extract, paywall_signal | 
homedy_com | homedy.com | sitemap_then_article_extract, paywall_signal, login_signal, captcha_signal | 
hsx_vn | hsx.vn | playwright_fallback | 
imf_org | imf.org | html_then_trafilatura, paywall_signal, login_signal, captcha_signal | 
investing_com | investing.com | sitemap_then_article_extract, paywall_signal | 
kinhtechungkhoan_vn | kinhtechungkhoan.vn | playwright_fallback, paywall_signal | 
kinhtedothi_vn | kinhtedothi.vn | manual_review | [WinError 10060] A connection attempt failed because the connected party did not properly respond after a period of time, or established connection failed because connected host has failed to respond 
kitco_com | kitco.com | sitemap_then_article_extract, paywall_signal | 
laodong_vn | laodong.vn | playwright_fallback | 

## Next Steps

- crawl sample active sources
- review metadata_only
- add API adapters for top official sources
- expand sources after v1 stable
