-- LeonQuant: Chuyên mục kinh tế đầu tư — 24h hot events + GKG themes (English regex only).
-- URLs per GlobalEventID from eventmentions; final filter: market_relevance_score >= 2 (not primary_sector).

WITH
  RankedTopEvents AS (
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
      DATEADDED
    FROM `gdelt-bq.gdeltv2.events_partitioned`
    WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      AND NumArticles >= 30
      AND ABS(AvgTone) >= 3.5
      AND SOURCEURL IS NOT NULL
      AND STARTS_WITH(SOURCEURL, 'http')
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY GLOBALEVENTID
      ORDER BY NumArticles DESC, ABS(AvgTone) DESC
    ) = 1
  ),

  TopEvents AS (
    SELECT *
    FROM RankedTopEvents
    ORDER BY NumArticles DESC, ABS(AvgTone) DESC
    LIMIT 500
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
        r'(youtube\.com|facebook\.com|x\.com|twitter\.com|tiktok\.com|instagram\.com)'
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

  EventSources AS (
    SELECT
      e.GLOBALEVENTID,
      e.Actor1Name,
      e.Actor2Name,
      e.EventRootCode,
      e.EventCode,
      e.GoldsteinScale,
      e.AvgTone,
      e.NumArticles,
      e.SOURCEURL,
      e.DATEADDED,

      ARRAY_AGG(
        m.MentionURL IGNORE NULLS
        ORDER BY m.MentionTimeDate DESC
        LIMIT 20
      ) AS SourceURLs,

      ARRAY_AGG(
        DISTINCT m.MentionSourceName IGNORE NULLS
        LIMIT 10
      ) AS MentionSources,

      COUNT(DISTINCT m.MentionURL) AS source_count

    FROM TopEvents AS e
    LEFT JOIN DedupMentions AS m
      ON e.GLOBALEVENTID = m.GLOBALEVENTID
    GROUP BY
      e.GLOBALEVENTID,
      e.Actor1Name,
      e.Actor2Name,
      e.EventRootCode,
      e.EventCode,
      e.GoldsteinScale,
      e.AvgTone,
      e.NumArticles,
      e.SOURCEURL,
      e.DATEADDED
  ),

  EventDocs AS (
    SELECT
      GLOBALEVENTID,
      SOURCEURL AS url,
      DATEADDED AS doc_time,
      1 AS is_primary
    FROM TopEvents
    WHERE SOURCEURL IS NOT NULL
      AND STARTS_WITH(SOURCEURL, 'http')

    UNION DISTINCT

    SELECT
      GLOBALEVENTID,
      MentionURL AS url,
      MentionTimeDate AS doc_time,
      0 AS is_primary
    FROM DedupMentions
    WHERE MentionURL IS NOT NULL
      AND STARTS_WITH(MentionURL, 'http')
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
      ARRAY_TO_STRING(
        ARRAY_AGG(DISTINCT V2Themes IGNORE NULLS LIMIT 50),
        ';'
      ) AS V2Themes,
      ARRAY_TO_STRING(
        ARRAY_AGG(DISTINCT V2Organizations IGNORE NULLS LIMIT 50),
        ';'
      ) AS V2Organizations,
      ARRAY_TO_STRING(
        ARRAY_AGG(DISTINCT V2Persons IGNORE NULLS LIMIT 50),
        ';'
      ) AS V2Persons,
      ARRAY_TO_STRING(
        ARRAY_AGG(DISTINCT V2Locations IGNORE NULLS LIMIT 50),
        ';'
      ) AS V2Locations
    FROM EventGKG
    GROUP BY GLOBALEVENTID
  ),

  BaseClassify AS (
    SELECT
      e.GLOBALEVENTID AS GlobalEventID,
      e.Actor1Name AS Doi_Tuong_Chinh,
      e.Actor2Name,
      e.EventRootCode,
      e.EventCode,
      e.GoldsteinScale,
      e.AvgTone AS Diem_Cam_Xuc,
      e.NumArticles AS So_Bao_De_Cap,
      e.SOURCEURL AS Link_Bai_Bao,
      e.DATEADDED,

      IF(
        ARRAY_LENGTH(COALESCE(e.SourceURLs, ARRAY<STRING>[])) > 0,
        e.SourceURLs,
        [e.SOURCEURL]
      ) AS SourceURLs,

      COALESCE(e.MentionSources, ARRAY<STRING>[]) AS MentionSources,

      IF(e.source_count > 0, e.source_count, 1) AS source_count,

      COALESCE(g.V2Themes, '') AS V2Themes,
      COALESCE(g.V2Organizations, '') AS V2Organizations,
      COALESCE(g.V2Persons, '') AS V2Persons,
      COALESCE(g.V2Locations, '') AS V2Locations,

      UPPER(COALESCE(g.V2Themes, '')) AS theme_u,
      UPPER(COALESCE(g.V2Organizations, '')) AS org_u,
      UPPER(COALESCE(g.V2Persons, '')) AS person_u,
      UPPER(COALESCE(g.V2Locations, '')) AS loc_u

    FROM EventSources AS e
    LEFT JOIN AggregatedGKG AS g
      ON e.GLOBALEVENTID = g.GLOBALEVENTID
  ),

  Signals AS (
    SELECT
      *,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'MACROECONOM|GDP|GROWTH|RECESSION|DEPRESSION|SOFT[_ ]?LANDING|HARD[_ ]?LANDING|INFLATION|DISINFLATION|DEFLATION|STAGFLATION|\bCPI\b|\bPPI\b|INTEREST[_ ]?RATE|POLICY[_ ]?RATE|RATE[_ ]?HIKE|RATE[_ ]?CUT|CENTRAL[_ ]?BANK|CENTRALBANK|MONETARY[_ ]?POLICY|QUANTITATIVE[_ ]?EASING|\bQE\b|\bQT\b|FISCAL[_ ]?POLICY|BUDGET|DEFICIT|DEBT[_ ]?CEILING|UNEMPLOYMENT|PAYROLL|\bNFP\b|JOBLESS[_ ]?CLAIMS|WAGE[_ ]?GROWTH|\bPMI\b|\bISM\b|RETAIL[_ ]?SALES|CONSUMER[_ ]?CONFIDENCE|YIELD[_ ]?CURVE|FOREIGN[_ ]?EXCHANGE|\bFX\b|\bUSD\b|DOLLAR|ECON_WORLDCURRENCIES|\b(FED|FOMC|FEDERAL RESERVE|ECB|BOJ|PBOC|BOE|IMF|WORLD BANK)\b'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(FED|FOMC|FEDERAL RESERVE|ECB|BOJ|PBOC|BOE|IMF|WORLD BANK)\b'
        )
      ) AS is_macro,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'FINANCE|FINANCIAL|BANKING|\bBANK\b|BANK[_ ]?RUN|DEPOSIT|WITHDRAWAL|CREDIT|LOAN|DEBT|SOVEREIGN[_ ]?DEBT|CORPORATE[_ ]?DEBT|\bBOND\b|TREASUR(Y|IES)|YIELD|HIGH[_ ]?YIELD|JUNK[_ ]?BOND|DEFAULT|INSOLVENCY|BANKRUPTCY|CHAPTER[_ ]?11|LIQUIDITY|BAILOUT|LEVERAGE|COLLATERAL|CREDIT[_ ]?RATING|RATING[_ ]?DOWNGRADE|\bCDS\b|CREDIT[_ ]?RISK|CAPITAL[_ ]?REQUIREMENT'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(JPMORGAN|JP MORGAN|GOLDMAN SACHS|MORGAN STANLEY|CITIGROUP|CITI|HSBC|UBS|FITCH|MOODY)\b'
        )
      ) AS is_credit_banking,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'STOCK[_ ]?MARKET|STOCK[_ ]?EXCHANGE|EQUITY|EQUITIES|\bSHARE\b|SHARES|WALL[_ ]?STREET|\bNYSE\b|\bNASDAQ\b|DOW[_ ]?JONES|S[_& ]?P|SP500|S&P500|RUSSELL|NIKKEI|FTSE|DAX|\bVIX\b|VOLATILITY|MARKET[_ ]?RALLY|SELL[_ ]?OFF|CORRECTION|EARNINGS|GUIDANCE|PROFIT[_ ]?WARNING|DIVIDEND|SHARE[_ ]?BUYBACK|IPO|SPAC|MERGER|ACQUISITION|TAKEOVER|ETF|HEDGE[_ ]?FUND'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(MSCI|BLACKROCK|VANGUARD|STATE STREET|BERKSHIRE)\b'
        )
      ) AS is_equity_market,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'CRYPTOCURRENCY|\bCRYPTO\b|BITCOIN|\bBTC\b|ETHEREUM|\bETH\b|BLOCKCHAIN|DIGITAL[_ ]?ASSET|DIGITAL[_ ]?CURRENCY|VIRTUAL[_ ]?CURRENCY|STABLECOIN|STABLECOINS|DEFI|DECENTRALIZED[_ ]?FINANCE|WEB3|ALTCOIN|TOKEN|NFT|SMART[_ ]?CONTRACT|SPOT[_ ]?ETF|CRYPTO[_ ]?EXCHANGE'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(BINANCE|COINBASE|TETHER|RIPPLE|KRAKEN|GRAYSCALE|BITWISE)\b'
        )
      ) AS is_crypto,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'COMMODIT|ENERGY|\bOIL\b|_OIL|OIL_|CRUDE|CRUDE[_ ]?OIL|BRENT|WTI|PETROLEUM|REFINERY|PIPELINE|FUEL|DIESEL|GASOLINE|NATURAL[_ ]?GAS|NATURALGAS|\bLNG\b|COAL|ELECTRICITY|POWER[_ ]?GRID|NUCLEAR[_ ]?ENERGY|OPEC|GOLD|SILVER|COPPER|LITHIUM|URANIUM|IRON[_ ]?ORE|STEEL|RARE[_ ]?EARTH|RARE[_ ]?EARTHS|MINING|MINERAL|WHEAT|CORN|SOYBEAN|SOYBEANS|COFFEE|COCOA|SUGAR'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(ARAMCO|EXXON|CHEVRON|SHELL|BP|TOTALENERGIES|GAZPROM|ROSNEFT|TRANSNEFT|BHP|RIO TINTO|VALE|GLENCORE)\b'
        )
      ) AS is_commodity_energy,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'TRADE[_ ]?DISPUTE|TRADE[_ ]?WAR|TARIFF|TARIFFS|SANCTION|SANCTIONS|EMBARGO|EXPORT[_ ]?CONTROL|EXPORT[_ ]?CONTROLS|EXPORT[_ ]?BAN|IMPORT[_ ]?RESTRICTION|TRADE[_ ]?RESTRICTION|SUPPLY[_ ]?CHAIN|SUPPLYCHAIN|LOGISTICS|SHIPPING|CONTAINER|FREIGHT|CARGO|CUSTOMS|PORT|PORTS|MARITIME|CANAL|SUEZ|PANAMA[_ ]?CANAL|RED[_ ]?SEA|HORMUZ|STRAIT[_ ]?OF[_ ]?HORMUZ|BAB[_ ]?EL[_ ]?MANDEB|BLACK[_ ]?SEA|RAIL|TRUCKING|AIR[_ ]?FREIGHT|WAREHOUSE|INVENTORY'
        )
        OR REGEXP_CONTAINS(
          loc_u,
          r'RED SEA|SUEZ|PANAMA CANAL|HORMUZ|BLACK SEA'
        )
      ) AS is_trade_supply,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'REAL[_ ]?ESTATE|REALESTATE|PROPERTY|HOUSING|MORTGAGE|COMMERCIAL[_ ]?REAL[_ ]?ESTATE|COMMERCIAL[_ ]?PROPERTY|OFFICE[_ ]?PROPERTY|\bREIT\b|RENT|RENTAL|HOME[_ ]?BUILD|HOMEBUILD|CONSTRUCTION|INFRASTRUCTURE|URBAN|BUILDING|BRIDGE|ROAD|RAIL|AIRPORT|METRO'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(EVERGRANDE|COUNTRY GARDEN|VANKE|BLACKSTONE|BROOKFIELD|PROLOGIS|CBRE|JLL|ZILLOW)\b'
        )
      ) AS is_real_estate_infra,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'TECHNOLOGY|ARTIFICIAL[_ ]?INTELLIGENCE|\bAI\b|GENERATIVE[_ ]?AI|\bLLM\b|MACHINE[_ ]?LEARNING|ROBOTICS|AUTONOMOUS|SOFTWARE|HARDWARE|SEMICONDUCTOR|SEMICONDUCTORS|\bCHIP\b|CHIPS|ADVANCED[_ ]?CHIPS|\bGPU\b|DATA[_ ]?CENTER|DATACENTER|CLOUD|CYBERSECURITY|CYBER[_ ]?ATTACK|RANSOMWARE|MALWARE|DATA[_ ]?BREACH|DIGITAL|PLATFORM|TELECOM|5G|QUANTUM'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(NVIDIA|TSMC|ASML|AMD|INTEL|OPENAI|MICROSOFT|GOOGLE|ALPHABET|META|AMAZON|APPLE|BROADCOM|ARM|QUALCOMM)\b'
        )
      ) AS is_tech_ai_chip,
      REGEXP_CONTAINS(
        theme_u,
        r'BUSINESS|COMPANY|CORPORATE|INDUSTRY|INDUSTRIAL|MANUFACTURING|FACTORY|FACTORY[_ ]?ORDERS|DURABLE[_ ]?GOODS|PRODUCTION|CAPEX|INVENTORY|WHOLESALE|RETAIL|RETAIL[_ ]?SALES|CONSUMER|SALES|REVENUE|PROFIT|MARGIN|EARNINGS[_ ]?GUIDANCE|LAYOFF|LAYOFFS|JOB[_ ]?CUTS|AUTO|EV|AIRLINE|TOURISM|HOTEL|RESTAURANT'
      ) AS is_real_economy,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'\bLAW\b|LEGAL|LEGISLATION|REGULATION|REGULATORY|ANTITRUST|LAWSUIT|LITIGATION|COURT|JUDGE|TRIAL|SUBPOENA|INDICTMENT|PROSECUT|INVESTIGATION|SEIZURE|SETTLEMENT|FINE|PENALTY|COMPLIANCE|FRAUD|CORRUPTION|MONEY[_ ]?LAUNDERING|EXPORT[_ ]?BAN'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(SEC|CFTC|DOJ|FCA|ESMA|FINRA|FTC|SUPREME COURT|EUROPEAN COMMISSION)\b'
        )
      ) AS is_legal_regulatory,
      REGEXP_CONTAINS(
        theme_u,
        r'WAR|CONFLICT|MILITARY|MISSILE|DRONE|ATTACK|TERROR|TERRORISM|CRISIS|COUP|UNREST|PROTEST|RIOT|BORDER|INVASION|ESCALATION|CEASEFIRE|NATO|DEFENSE|SECURITY'
      ) AS is_conflict_security,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'POLITICAL|POLITICS|GOVERNMENT|GENERAL[_ ]?GOVERNMENT|PRESIDENT|PRIME[_ ]?MINISTER|MINISTER|PARLIAMENT|CONGRESS|SENATE|CABINET|LEADER|ELECTION|VOTE|REFERENDUM|DIPLOMACY|FOREIGN[_ ]?POLICY|GEOPOLITICS|TREATY|SUMMIT|G7|G20|BRICS|UNITED[_ ]?NATIONS'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(NATO|BRICS|G7|G20|UNITED NATIONS|UN|EUROPEAN UNION)\b'
        )
      ) AS is_politics_diplomacy
    FROM BaseClassify
  ),

  Classified AS (
    SELECT
      *,
      CASE
        WHEN is_macro THEN 'Vĩ mô - Chính sách Tiền tệ & Lãi suất'
        WHEN is_credit_banking THEN 'Tài chính - Ngân hàng & Tín dụng'
        WHEN is_equity_market THEN 'Chứng khoán - Thị trường Vốn'
        WHEN is_crypto THEN 'Crypto - Tiền mã hóa & Tài sản số'
        WHEN is_commodity_energy THEN 'Hàng hóa - Năng lượng & Khoáng sản'
        WHEN is_trade_supply THEN 'Thương mại - Chuỗi cung ứng Toàn cầu'
        WHEN is_real_estate_infra THEN 'Bất động sản - Hạ tầng'
        WHEN is_tech_ai_chip THEN 'Công nghệ - AI & Bán dẫn'
        WHEN is_real_economy THEN 'Doanh nghiệp - Công nghiệp & Tiêu dùng'
        WHEN is_legal_regulatory THEN 'Pháp lý - Quy định & Trừng phạt'
        WHEN is_conflict_security THEN 'Khủng hoảng - Xung đột & An ninh'
        WHEN is_politics_diplomacy THEN 'Chính trị - Ngoại giao'
        ELSE 'Khác'
      END AS primary_sector
    FROM Signals
  ),

  FinalClassified AS (
    SELECT
      *,
      CASE
        WHEN is_conflict_security AND primary_sector != 'Khủng hoảng - Xung đột & An ninh'
          THEN 'Khủng hoảng - Xung đột & An ninh'
        WHEN is_legal_regulatory AND primary_sector != 'Pháp lý - Quy định & Trừng phạt'
          THEN 'Pháp lý - Quy định & Trừng phạt'
        WHEN is_trade_supply AND primary_sector != 'Thương mại - Chuỗi cung ứng Toàn cầu'
          THEN 'Thương mại - Chuỗi cung ứng Toàn cầu'
        WHEN is_politics_diplomacy AND primary_sector != 'Chính trị - Ngoại giao'
          THEN 'Chính trị - Ngoại giao'
        ELSE NULL
      END AS secondary_sector,
      ARRAY(
        SELECT flag
        FROM UNNEST([
          IF(is_conflict_security, 'conflict_security_risk', NULL),
          IF(is_legal_regulatory, 'legal_regulatory_risk', NULL),
          IF(is_credit_banking, 'credit_liquidity_risk', NULL),
          IF(
            is_macro
            AND REGEXP_CONTAINS(theme_u, r'INTEREST|RATE|YIELD|TREASUR|CENTRAL[_ ]?BANK|MONETARY'),
            'rate_policy_risk',
            NULL
          ),
          IF(
            is_macro
            AND REGEXP_CONTAINS(theme_u, r'INFLATION|CPI|PPI|STAGFLATION'),
            'inflation_risk',
            NULL
          ),
          IF(is_commodity_energy, 'commodity_energy_risk', NULL),
          IF(is_trade_supply, 'supply_chain_risk', NULL),
          IF(is_real_estate_infra, 'real_estate_infra_risk', NULL),
          IF(is_crypto, 'crypto_risk', NULL),
          IF(
            is_tech_ai_chip
            AND REGEXP_CONTAINS(theme_u, r'CYBER|HACK|RANSOMWARE|DATA[_ ]?BREACH|MALWARE'),
            'cyber_risk',
            NULL
          )
        ]) AS flag
        WHERE flag IS NOT NULL
      ) AS risk_flags,
      CASE
        WHEN (
          is_conflict_security
          OR is_credit_banking
          OR is_legal_regulatory
          OR (
            is_macro
            AND REGEXP_CONTAINS(theme_u, r'RATE[_ ]?HIKE|INFLATION|STAGFLATION|RECESSION|HARD[_ ]?LANDING')
          )
          OR Diem_Cam_Xuc <= -6
        )
        AND (
          REGEXP_CONTAINS(theme_u, r'RATE[_ ]?CUT|DISINFLATION|SOFT[_ ]?LANDING|EARNINGS|MARKET[_ ]?RALLY|GROWTH')
          OR Diem_Cam_Xuc >= 6
        )
          THEN 'mixed'
        WHEN (
          is_conflict_security
          OR is_credit_banking
          OR is_legal_regulatory
          OR (
            is_macro
            AND REGEXP_CONTAINS(theme_u, r'RATE[_ ]?HIKE|INFLATION|STAGFLATION|RECESSION|HARD[_ ]?LANDING')
          )
          OR Diem_Cam_Xuc <= -6
        )
          THEN 'risk_off'
        WHEN (
          REGEXP_CONTAINS(theme_u, r'RATE[_ ]?CUT|DISINFLATION|SOFT[_ ]?LANDING|EARNINGS|MARKET[_ ]?RALLY|GROWTH')
          OR Diem_Cam_Xuc >= 6
        )
          THEN 'risk_on'
        ELSE 'neutral'
      END AS macro_signal,
      (
        IF(is_macro, 3, 0)
        + IF(is_credit_banking, 3, 0)
        + IF(is_equity_market, 3, 0)
        + IF(is_crypto, 3, 0)
        + IF(is_commodity_energy, 3, 0)
        + IF(is_trade_supply, 2, 0)
        + IF(is_tech_ai_chip, 2, 0)
        + IF(is_real_estate_infra, 1, 0)
        + IF(is_real_economy, 1, 0)
        + IF(
            (is_conflict_security OR is_politics_diplomacy OR is_legal_regulatory)
            AND REGEXP_CONTAINS(
              theme_u,
              r'\bOIL\b|CRUDE|BRENT|WTI|NATURAL[_ ]?GAS|\bLNG\b|ENERGY|SANCTION|TARIFF|SUPPLY[_ ]?CHAIN|BANK|CREDIT|LIQUIDITY|TREASUR|YIELD|\bUSD\b|DOLLAR|INFLATION|INTEREST[_ ]?RATE|SEMICONDUCTOR|\bCHIP\b|TRADE'
            ),
            1,
            0
          )
        - IF(
            (is_conflict_security OR is_politics_diplomacy OR is_legal_regulatory)
            AND NOT (
              is_macro OR is_credit_banking OR is_equity_market OR is_crypto OR
              is_commodity_energy OR is_trade_supply OR is_tech_ai_chip OR
              is_real_estate_infra OR is_real_economy
            ),
            3,
            0
          )
      ) AS market_relevance_score,
      ARRAY(
        SELECT asset
        FROM UNNEST(ARRAY_CONCAT(
          IF(is_equity_market OR is_real_economy OR is_tech_ai_chip, ['stocks'], []),
          IF(is_macro OR is_credit_banking, ['bonds'], []),
          IF(
            REGEXP_CONTAINS(theme_u, r'DOLLAR|\bUSD\b|FOREIGN[_ ]?EXCHANGE|\bFX\b|CURRENCY'),
            ['USD'],
            []
          ),
          IF(
            is_commodity_energy
            AND REGEXP_CONTAINS(theme_u, r'GOLD|SILVER|PRECIOUS'),
            ['gold'],
            []
          ),
          IF(
            is_commodity_energy
            AND REGEXP_CONTAINS(theme_u, r'\bOIL\b|CRUDE|BRENT|WTI|PETROLEUM|OPEC'),
            ['oil'],
            []
          ),
          IF(
            is_commodity_energy
            AND REGEXP_CONTAINS(theme_u, r'NATURAL[_ ]?GAS|NATURALGAS|\bLNG\b'),
            ['gas'],
            []
          ),
          IF(is_crypto, ['crypto'], []),
          IF(is_real_estate_infra, ['real_estate'], []),
          IF(is_credit_banking, ['banks'], [])
        )) AS asset
      ) AS affected_assets,
      CASE
        WHEN So_Bao_De_Cap >= 80 OR ABS(Diem_Cam_Xuc) >= 8 OR is_conflict_security OR is_credit_banking
          THEN 'high'
        WHEN So_Bao_De_Cap >= 40 OR ABS(Diem_Cam_Xuc) >= 4
          THEN 'medium'
        ELSE 'low'
      END AS investment_relevance
    FROM Classified
  )

SELECT
  GlobalEventID,
  Doi_Tuong_Chinh,
  Actor2Name,
  EventRootCode,
  EventCode,
  GoldsteinScale,
  Diem_Cam_Xuc,
  So_Bao_De_Cap,
  Link_Bai_Bao,
  SourceURLs,
  MentionSources,
  source_count,
  primary_sector AS Nhom_Nganh,
  primary_sector,
  secondary_sector,
  risk_flags,
  macro_signal,
  affected_assets,
  investment_relevance,
  market_relevance_score,
  REGEXP_REPLACE(COALESCE(V2Organizations, ''), r',?\d+', '') AS Cac_To_Chuc_Lien_Quan,
  V2Themes,
  V2Persons,
  V2Locations
FROM FinalClassified
WHERE market_relevance_score >= 2
ORDER BY
  market_relevance_score DESC,
  So_Bao_De_Cap DESC,
  ABS(Diem_Cam_Xuc) DESC,
  source_count DESC
LIMIT 100
