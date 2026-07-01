-- LeonQuant standalone technology & AI pulse
-- Principles:
-- 1. TopEvents first.
-- 2. EventMentions provide real article URLs.
-- 3. GKG joins only after TopEvents are chosen.
-- 4. AvgTone is ranking only, not a hard gate.

WITH
  CandidateBaseEvents AS (
    SELECT
      GLOBALEVENTID,
      Actor1Name,
      Actor2Name,
      EventRootCode,
      EventCode,
      GoldsteinScale,
      AvgTone,
      NumArticles,
      SOURCEURL,
      DATEADDED,
      UPPER(
        CONCAT(
          COALESCE(Actor1Name, ''), ' ',
          COALESCE(Actor2Name, ''), ' ',
          COALESCE(SOURCEURL, '')
        )
      ) AS event_hint_u
    FROM `gdelt-bq.gdeltv2.events_partitioned`
    WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      AND SOURCEURL IS NOT NULL
      AND STARTS_WITH(SOURCEURL, 'http')
      AND NOT REGEXP_CONTAINS(
        LOWER(SOURCEURL),
        r'(youtube\.com|youtu\.be|facebook\.com|instagram\.com|x\.com|twitter\.com|tiktok\.com|linkedin\.com|prnewswire\.com|businesswire\.com|globenewswire\.com)'
      )
  ),

  CandidateScored AS (
    SELECT
      *,
      REGEXP_CONTAINS(
        event_hint_u,
        r'ARTIFICIAL[ _-]?INTELLIGENCE|GENERATIVE[ _-]?AI|GENAI|FOUNDATION[ _-]?MODEL|FRONTIER[ _-]?MODEL|LARGE[ _-]?(LANGUAGE|MULTIMODAL)[ _-]?MODEL|(^|[^A-Z0-9])LLM([^A-Z0-9]|$)|AI[ _-]?AGENT|AGENTIC[ _-]?AI|REASONING[ _-]?MODEL|MULTIMODAL[ _-]?MODEL|MODEL[ _-]?CONTEXT[ _-]?PROTOCOL|OPEN[ _-]?WEIGHTS'
      ) AS has_core_ai,
      REGEXP_CONTAINS(
        event_hint_u,
        r'OPENAI|CHATGPT|ANTHROPIC|CLAUDE|DEEPMIND|GEMINI|META[ _-]?AI|LLAMA|MICROSOFT[ _-]?COPILOT|GITHUB[ _-]?COPILOT|NVIDIA|XAI|GROK|MISTRAL|COHERE|HUGGING[ _-]?FACE|STABILITY[ _-]?AI|MIDJOURNEY|RUNWAY|PERPLEXITY|DEEPSEEK|QWEN|ALIBABA|BAIDU|ERNIE|TENCENT|HUNYUAN|HUAWEI|PANGU|BYTEDANCE|DOUBAO|ZHIPU|MINIMAX|MOONSHOT|KIMI|SENSETIME|IFLYTEK|HYPERCLOVA|YANDEXGPT|GIGACHAT|FALCON[ _-]?LLM|MBZUAI|CEREBRAS|GROQ|SAMBANOVA|COREWEAVE|DATABRICKS|OPENROUTER|LANGCHAIN|LLAMAINDEX|OLLAMA|VLLM|PYTORCH|TENSORFLOW'
      ) AS has_entity,
      REGEXP_CONTAINS(
        event_hint_u,
        r'LAUNCH(ES|ED)?|RELEASE(S|D)?|INTRODUC(ES|ED)|UNVEIL(S|ED)?|ANNOUNC(ES|ED)?|OPEN[ _-]?SOURC(ES|ED|ING)|UPDAT(ES|ED)|UPGRAD(ES|ED)|PREVIEW|BETA|GENERAL[ _-]?AVAILABILITY|BENCHMARK|FUNDING|RAISES|ACQUIR(ES|ED)|ACQUISITION|PARTNERSHIP|DEPLOY(S|ED)?|ADOPT(S|ED)?|BAN(S|NED)?|REGULAT(ES|ED)|INVESTIGAT(ES|ED)|VULNERABILITY'
      ) AS has_action,
      REGEXP_CONTAINS(
        event_hint_u,
        r'AI[ _-]?(CHIP|ACCELERATOR|SERVER)|GPU|NPU|TPU|SEMICONDUCTOR|FOUNDRY|WAFER|LITHOGRAPHY|HBM|CHIPLET|ADVANCED[ _-]?PACKAGING|DATA[ _-]?CENTER|SUPERCOMPUTER|CLOUD[ _-]?COMPUTING|EDGE[ _-]?COMPUTING|KUBERNETES|DOCKER|MLOPS|VECTOR[ _-]?DATABASE|OPEN[ _-]?SOURCE|CYBER[ _-]?SECURITY|RANSOMWARE|ZERO[ _-]?DAY|DATA[ _-]?BREACH|PROMPT[ _-]?INJECTION|ROBOTICS|HUMANOID[ _-]?ROBOT|EMBODIED[ _-]?AI|AUTONOMOUS[ _-]?(VEHICLE|DRIVING)|ROBOTAXI|DRONE|QUANTUM[ _-]?(COMPUTING|COMPUTER|PROCESSOR|CHIP)|(^|[^A-Z0-9])6G([^A-Z0-9]|$)|SPATIAL[ _-]?COMPUTING'
      ) AS has_sector,
      REGEXP_CONTAINS(
        event_hint_u,
        r'AI[ _-]?(ACT|REGULATION|SAFETY|GOVERNANCE)|MODEL[ _-]?SAFETY|ALGORITHMIC[ _-]?ACCOUNTABILITY|TRAINING[ _-]?DATA|COPYRIGHT|EXPORT[ _-]?CONTROL|CHIP[ _-]?(EXPORT|SANCTION)|SEMICONDUCTOR[ _-]?SANCTION|TECH[ _-]?SOVEREIGNTY|SOVEREIGN[ _-]?AI'
      ) AS has_policy,
      REGEXP_CONTAINS(
        LOWER(SOURCEURL),
        r'/(ai|artificial-intelligence|machine-learning|deep-learning|generative-ai|llm|agents?|semiconductor|chips?|gpu|data-center|cloud|developer|open-source|cybersecurity|security|robotics?|autonomous|quantum|telecom|spatial-computing)(/|-|_)'
      ) AS has_url_hint
    FROM CandidateBaseEvents
  ),

  CandidateRanked AS (
    SELECT
      *,
      CASE
        WHEN NumArticles >= 8 AND (has_core_ai OR (has_entity AND has_action)) THEN 'pool_a'
        WHEN NumArticles >= 12 AND has_sector THEN 'pool_b'
        WHEN NumArticles >= 10 AND has_policy THEN 'pool_c'
        WHEN NumArticles >= 35 AND has_url_hint THEN 'pool_d'
        ELSE 'other'
      END AS pool_kind,
      CASE
        WHEN NumArticles >= 8 AND (has_core_ai OR (has_entity AND has_action)) THEN 1
        WHEN NumArticles >= 12 AND has_sector THEN 2
        WHEN NumArticles >= 10 AND has_policy THEN 3
        WHEN NumArticles >= 35 AND has_url_hint THEN 4
        ELSE 9
      END AS pool_priority
    FROM CandidateScored
  ),

  TopEvents AS (
    SELECT *
    FROM CandidateRanked
    WHERE pool_kind != 'other'
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY GLOBALEVENTID
      ORDER BY pool_priority, NumArticles DESC, ABS(AvgTone) DESC, DATEADDED DESC
    ) = 1
    ORDER BY pool_priority, NumArticles DESC, DATEADDED DESC, ABS(AvgTone) DESC
    LIMIT 180
  ),

  FilteredMentions AS (
    SELECT
      m.GLOBALEVENTID,
      m.MentionIdentifier AS MentionURL,
      m.MentionSourceName,
      m.MentionTimeDate
    FROM `gdelt-bq.gdeltv2.eventmentions_partitioned` AS m
    INNER JOIN TopEvents AS e
      ON m.GLOBALEVENTID = e.GLOBALEVENTID
    WHERE m._PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      AND m.MentionIdentifier IS NOT NULL
      AND STARTS_WITH(m.MentionIdentifier, 'http')
      AND NOT REGEXP_CONTAINS(
        LOWER(m.MentionIdentifier),
        r'(youtube\.com|youtu\.be|facebook\.com|instagram\.com|x\.com|twitter\.com|tiktok\.com|linkedin\.com|prnewswire\.com|businesswire\.com|globenewswire\.com)'
      )
  ),

  DedupMentions AS (
    SELECT *
    FROM FilteredMentions
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY GLOBALEVENTID, MentionURL
      ORDER BY MentionTimeDate DESC
    ) = 1
  ),

  EventDocs AS (
    SELECT GLOBALEVENTID, SOURCEURL AS url, DATEADDED AS doc_time, 1 AS is_primary
    FROM TopEvents
    UNION DISTINCT
    SELECT GLOBALEVENTID, MentionURL AS url, MentionTimeDate AS doc_time, 0 AS is_primary
    FROM DedupMentions
  ),

  LimitedEventDocs AS (
    SELECT *
    FROM EventDocs
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY GLOBALEVENTID
      ORDER BY is_primary DESC, doc_time DESC, url
    ) <= 12
  ),

  EventGKG AS (
    SELECT
      d.GLOBALEVENTID,
      g.DocumentIdentifier,
      g.V2Themes,
      g.V2Organizations,
      g.V2Persons,
      g.V2Locations
    FROM LimitedEventDocs AS d
    INNER JOIN `gdelt-bq.gdeltv2.gkg_partitioned` AS g
      ON g.DocumentIdentifier = d.url
     AND g._PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    WHERE g.DocumentIdentifier IS NOT NULL
  ),

  AggregatedGKG AS (
    SELECT
      GLOBALEVENTID,
      ARRAY_TO_STRING(ARRAY_AGG(DISTINCT V2Themes IGNORE NULLS LIMIT 60), ';') AS V2Themes,
      ARRAY_TO_STRING(ARRAY_AGG(DISTINCT V2Organizations IGNORE NULLS LIMIT 60), ';') AS V2Organizations,
      ARRAY_TO_STRING(ARRAY_AGG(DISTINCT V2Persons IGNORE NULLS LIMIT 60), ';') AS V2Persons,
      ARRAY_TO_STRING(ARRAY_AGG(DISTINCT V2Locations IGNORE NULLS LIMIT 60), ';') AS V2Locations
    FROM EventGKG
    GROUP BY GLOBALEVENTID
  ),

  FinalRows AS (
    SELECT
      e.GLOBALEVENTID AS GlobalEventID,
      e.Actor1Name,
      e.Actor2Name,
      e.EventRootCode,
      e.EventCode,
      e.GoldsteinScale,
      e.AvgTone,
      e.NumArticles,
      e.SOURCEURL AS Link_Bai_Bao,
      e.DATEADDED,
      e.pool_kind,
      IF(
        ARRAY_LENGTH(ARRAY_AGG(m.MentionURL IGNORE NULLS ORDER BY m.MentionTimeDate DESC LIMIT 20)) > 0,
        ARRAY_AGG(m.MentionURL IGNORE NULLS ORDER BY m.MentionTimeDate DESC LIMIT 20),
        [e.SOURCEURL]
      ) AS SourceURLs,
      COUNT(DISTINCT m.MentionURL) AS source_count,
      ARRAY_AGG(DISTINCT m.MentionSourceName IGNORE NULLS LIMIT 10) AS MentionSources,
      COALESCE(g.V2Themes, '') AS V2Themes,
      COALESCE(g.V2Organizations, '') AS V2Organizations,
      COALESCE(g.V2Persons, '') AS V2Persons,
      COALESCE(g.V2Locations, '') AS V2Locations
    FROM TopEvents AS e
    LEFT JOIN DedupMentions AS m
      ON e.GLOBALEVENTID = m.GLOBALEVENTID
    LEFT JOIN AggregatedGKG AS g
      ON e.GLOBALEVENTID = g.GLOBALEVENTID
    GROUP BY
      GlobalEventID, Actor1Name, Actor2Name, EventRootCode, EventCode,
      GoldsteinScale, AvgTone, NumArticles, Link_Bai_Bao, DATEADDED,
      pool_kind, V2Themes, V2Organizations, V2Persons, V2Locations
  )

SELECT *
FROM FinalRows
ORDER BY source_count DESC, NumArticles DESC, DATEADDED DESC, ABS(AvgTone) DESC
LIMIT 120
