-- Standalone Technology and AI desk, latest 72 hours.
-- Cost controls: partition filters on every public table, TopEvents before mentions/GKG,
-- capped event documents and final rows. AvgTone is ranking only.
WITH
  CandidateBase AS (
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
      UPPER(CONCAT(
        COALESCE(Actor1Name, ''), ' ',
        COALESCE(Actor2Name, ''), ' ',
        COALESCE(SOURCEURL, '')
      )) AS hint
    FROM `gdelt-bq.gdeltv2.events_partitioned`
    WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 72 HOUR)
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
        hint,
        r'ARTIFICIAL[ _-]?INTELLIGENCE|GENERATIVE[ _-]?AI|GENAI|FOUNDATION[ _-]?MODEL|FRONTIER[ _-]?MODEL|LARGE[ _-]?(LANGUAGE|MULTIMODAL)[ _-]?MODEL|(^|[^A-Z0-9])LLM([^A-Z0-9]|$)|AI[ _-]?AGENT|AGENTIC[ _-]?AI|REASONING[ _-]?MODEL|MULTIMODAL[ _-]?MODEL|MODEL[ _-]?CONTEXT[ _-]?PROTOCOL|OPEN[ _-]?WEIGHTS'
      ) AS core_ai,
      REGEXP_CONTAINS(
        hint,
        r'OPENAI|CHATGPT|ANTHROPIC|CLAUDE|DEEPMIND|GEMINI|META[ _-]?AI|LLAMA|MICROSOFT[ _-]?COPILOT|GITHUB[ _-]?COPILOT|NVIDIA|XAI|GROK|MISTRAL|COHERE|HUGGING[ _-]?FACE|STABILITY[ _-]?AI|MIDJOURNEY|RUNWAY|PERPLEXITY|DEEPSEEK|QWEN|ALIBABA|BAIDU|ERNIE|TENCENT|HUNYUAN|HUAWEI|PANGU|BYTEDANCE|DOUBAO|ZHIPU|MINIMAX|MOONSHOT|KIMI|SENSETIME|IFLYTEK|HYPERCLOVA|YANDEXGPT|GIGACHAT|FALCON[ _-]?LLM|MBZUAI|CEREBRAS|GROQ|SAMBANOVA|COREWEAVE|DATABRICKS|OPENROUTER|LANGCHAIN|LLAMAINDEX|OLLAMA|VLLM|PYTORCH|TENSORFLOW'
      ) AS entity_signal,
      REGEXP_CONTAINS(
        hint,
        r'LAUNCH(ES|ED)?|RELEASE(S|D)?|INTRODUC(ES|ED)|UNVEIL(S|ED)?|ANNOUNC(ES|ED)?|OPEN[ _-]?SOURC(ES|ED|ING)|UPDAT(ES|ED)|UPGRAD(ES|ED)|PREVIEW|BETA|GENERAL[ _-]?AVAILABILITY|BENCHMARK|FUNDING|RAISES|ACQUIR(ES|ED)|ACQUISITION|PARTNERSHIP|DEPLOY(S|ED)?|ADOPT(S|ED)?|BAN(S|NED)?|REGULAT(ES|ED)|INVESTIGAT(ES|ED)|VULNERABILITY'
      ) AS action_signal,
      REGEXP_CONTAINS(
        hint,
        r'AI[ _-]?(CHIP|ACCELERATOR|SERVER)|GPU|NPU|TPU|SEMICONDUCTOR|FOUNDRY|WAFER|LITHOGRAPHY|HBM|CHIPLET|ADVANCED[ _-]?PACKAGING|DATA[ _-]?CENTER|SUPERCOMPUTER|CLOUD[ _-]?COMPUTING|EDGE[ _-]?COMPUTING|KUBERNETES|DOCKER|MLOPS|VECTOR[ _-]?DATABASE|OPEN[ _-]?SOURCE|CYBER[ _-]?SECURITY|DATA[ _-]?BREACH|PROMPT[ _-]?INJECTION|ROBOTICS|HUMANOID[ _-]?ROBOT|EMBODIED[ _-]?AI|AUTONOMOUS[ _-]?(VEHICLE|DRIVING)|ROBOTAXI|DRONE|QUANTUM[ _-]?(COMPUTING|COMPUTER|PROCESSOR|CHIP)|(^|[^A-Z0-9])6G([^A-Z0-9]|$)|SPATIAL[ _-]?COMPUTING'
      ) AS sector_signal,
      REGEXP_CONTAINS(
        hint,
        r'AI[ _-]?(ACT|REGULATION|SAFETY|GOVERNANCE)|MODEL[ _-]?SAFETY|ALGORITHMIC[ _-]?ACCOUNTABILITY|TRAINING[ _-]?DATA|COPYRIGHT|EXPORT[ _-]?CONTROL|CHIP[ _-]?(EXPORT|SANCTION)|SEMICONDUCTOR[ _-]?SANCTION|TECH[ _-]?SOVEREIGNTY|SOVEREIGN[ _-]?AI'
      ) AS policy_signal,
      REGEXP_CONTAINS(
        LOWER(SOURCEURL),
        r'/(ai|artificial-intelligence|machine-learning|deep-learning|generative-ai|llm|agents?|semiconductor|chips?|gpu|data-center|cloud|developer|open-source|cybersecurity|security|robotics?|autonomous|quantum|telecom|spatial-computing)(/|-|_)'
      ) AS url_signal
    FROM CandidateBase
  ),

  CandidatePools AS (
    SELECT
      *,
      CASE
        WHEN NumArticles >= 8 AND (core_ai OR (entity_signal AND action_signal)) THEN 'pool_a'
        WHEN NumArticles >= 12 AND sector_signal THEN 'pool_b'
        WHEN NumArticles >= 10 AND policy_signal THEN 'pool_c'
        WHEN NumArticles >= 35 AND url_signal THEN 'pool_d'
        ELSE 'other'
      END AS pool_kind,
      CASE
        WHEN NumArticles >= 8 AND (core_ai OR (entity_signal AND action_signal)) THEN 1
        WHEN NumArticles >= 12 AND sector_signal THEN 2
        WHEN NumArticles >= 10 AND policy_signal THEN 3
        WHEN NumArticles >= 35 AND url_signal THEN 4
        ELSE 9
      END AS pool_priority
    FROM CandidateScored
  ),

  RankedEvents AS (
    SELECT *
    FROM CandidatePools
    WHERE pool_kind != 'other'
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY GLOBALEVENTID
      ORDER BY pool_priority, NumArticles DESC, DATEADDED DESC, ABS(AvgTone) DESC
    ) = 1
  ),

  PoolCapped AS (
    SELECT *
    FROM RankedEvents
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY pool_kind
      ORDER BY NumArticles DESC, DATEADDED DESC, ABS(AvgTone) DESC
    ) <= CASE
      WHEN pool_kind = 'pool_a' THEN 70
      WHEN pool_kind = 'pool_b' THEN 50
      WHEN pool_kind = 'pool_c' THEN 35
      WHEN pool_kind = 'pool_d' THEN 25
      ELSE 0
    END
  ),

  TopEvents AS (
    SELECT *
    FROM PoolCapped
    ORDER BY pool_priority, NumArticles DESC, DATEADDED DESC
    LIMIT 150
  ),

  Mentions AS (
    SELECT
      m.GLOBALEVENTID,
      m.MentionIdentifier AS MentionURL,
      m.MentionSourceName,
      m.MentionTimeDate
    FROM `gdelt-bq.gdeltv2.eventmentions_partitioned` AS m
    INNER JOIN TopEvents AS e USING (GLOBALEVENTID)
    WHERE m._PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 72 HOUR)
      AND m.MentionIdentifier IS NOT NULL
      AND STARTS_WITH(m.MentionIdentifier, 'http')
      AND NOT REGEXP_CONTAINS(
        LOWER(m.MentionIdentifier),
        r'(youtube\.com|youtu\.be|facebook\.com|instagram\.com|x\.com|twitter\.com|tiktok\.com|linkedin\.com|prnewswire\.com|businesswire\.com|globenewswire\.com)'
      )
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY m.GLOBALEVENTID, m.MentionIdentifier
      ORDER BY m.MentionTimeDate DESC
    ) = 1
  ),

  EventDocs AS (
    SELECT GLOBALEVENTID, SOURCEURL AS url, DATEADDED AS doc_time, 1 AS primary_rank
    FROM TopEvents
    UNION ALL
    SELECT GLOBALEVENTID, MentionURL, MentionTimeDate, 0
    FROM Mentions
  ),

  LimitedDocs AS (
    SELECT *
    FROM EventDocs
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY GLOBALEVENTID
      ORDER BY primary_rank DESC, doc_time DESC, url
    ) <= 8
  ),

  EventGKG AS (
    SELECT
      d.GLOBALEVENTID,
      g.V2Themes,
      g.V2Organizations,
      g.V2Persons,
      g.V2Locations
    FROM LimitedDocs AS d
    INNER JOIN `gdelt-bq.gdeltv2.gkg_partitioned` AS g
      ON g.DocumentIdentifier = d.url
     AND g._PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 72 HOUR)
  ),

  AggregatedGKG AS (
    SELECT
      GLOBALEVENTID,
      ARRAY_TO_STRING(ARRAY_AGG(DISTINCT V2Themes IGNORE NULLS LIMIT 40), ';') AS V2Themes,
      ARRAY_TO_STRING(ARRAY_AGG(DISTINCT V2Organizations IGNORE NULLS LIMIT 40), ';') AS V2Organizations,
      ARRAY_TO_STRING(ARRAY_AGG(DISTINCT V2Persons IGNORE NULLS LIMIT 30), ';') AS V2Persons,
      ARRAY_TO_STRING(ARRAY_AGG(DISTINCT V2Locations IGNORE NULLS LIMIT 30), ';') AS V2Locations
    FROM EventGKG
    GROUP BY GLOBALEVENTID
  )

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
    COUNT(m.MentionURL) > 0,
    ARRAY_AGG(m.MentionURL IGNORE NULLS ORDER BY m.MentionTimeDate DESC LIMIT 12),
    [e.SOURCEURL]
  ) AS SourceURLs,
  COUNT(DISTINCT m.MentionURL) AS source_count,
  ARRAY_AGG(DISTINCT m.MentionSourceName IGNORE NULLS LIMIT 10) AS MentionSources,
  COALESCE(g.V2Themes, '') AS V2Themes,
  COALESCE(g.V2Organizations, '') AS V2Organizations,
  COALESCE(g.V2Persons, '') AS V2Persons,
  COALESCE(g.V2Locations, '') AS V2Locations
FROM TopEvents AS e
LEFT JOIN Mentions AS m USING (GLOBALEVENTID)
LEFT JOIN AggregatedGKG AS g USING (GLOBALEVENTID)
GROUP BY
  GlobalEventID, Actor1Name, Actor2Name, EventRootCode, EventCode,
  GoldsteinScale, AvgTone, NumArticles, Link_Bai_Bao, DATEADDED,
  pool_kind, V2Themes, V2Organizations, V2Persons, V2Locations
ORDER BY source_count DESC, NumArticles DESC, DATEADDED DESC, ABS(AvgTone) DESC
LIMIT 100
