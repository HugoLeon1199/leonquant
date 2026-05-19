import scrapy


class ArticleItem(scrapy.Item):
    source_id = scrapy.Field()
    url = scrapy.Field()
    discovered_at = scrapy.Field()
    candidate_published_at = scrapy.Field()
    discovery_source = scrapy.Field()
    target_date = scrapy.Field()
    is_today_candidate = scrapy.Field()
    title = scrapy.Field()
    published_at = scrapy.Field()
    content = scrapy.Field()
    content_length = scrapy.Field()
    content_hash = scrapy.Field()
    language = scrapy.Field()
    crawl_strategy_used = scrapy.Field()
    raw_path = scrapy.Field()
    quality_score = scrapy.Field()
    error_type = scrapy.Field()
    error_message = scrapy.Field()
    # Populated by spider before pipeline; stripped before persistence
    html_body = scrapy.Field()
    response_status = scrapy.Field()
    source_active = scrapy.Field()
