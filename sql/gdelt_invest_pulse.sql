-- LeonQuant: Chuyên mục kinh tế đầu tư — 24h hot events + GKG sector tags only.
-- URLs per GlobalEventID from eventmentions; economic relevance filtered in leon.py via Gemini (not SQL).

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
          r'MACROECONOM|GDP|GROWTH|RECESSION|DEPRESSION|SOFT[_ ]?LANDING|HARD[_ ]?LANDING|INFLATION|DISINFLATION|DEFLATION|STAGFLATION|\bCPI\b|\bPPI\b|INTEREST[_ ]?RATE|POLICY[_ ]?RATE|RATE[_ ]?HIKE|RATE[_ ]?CUT|CENTRAL[_ ]?BANK|CENTRALBANK|MONETARY[_ ]?POLICY|QUANTITATIVE[_ ]?EASING|\bQE\b|\bQT\b|FISCAL[_ ]?POLICY|BUDGET|DEFICIT|UNEMPLOYMENT|PAYROLL|\bNFP\b|YIELD[_ ]?CURVE|FOREIGN[_ ]?EXCHANGE|\bFX\b|DOLLAR|\bUSD\b|CURRENCY[_ ]?RESERVE|ECON_WORLDCURRENCIES'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(FED|FOMC|FEDERAL RESERVE|ECB|EUROPEAN CENTRAL BANK|BOJ|BANK OF JAPAN|PBOC|PEOPLE.?S BANK OF CHINA|SNB|BANK OF ENGLAND|BOE|IMF|WORLD BANK)\b'
        )
      ) AS is_macro,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'FINANCE|FINANCIAL|BANK|BANKING|BANK[_ ]?RUN|DEPOSIT|WITHDRAWAL|CREDIT|LOAN|DEBT|SOVEREIGN[_ ]?DEBT|CORPORATE[_ ]?DEBT|BOND|TREASUR(Y|IES)|YIELD|HIGH[_ ]?YIELD|JUNK[_ ]?BOND|DEFAULT|INSOLVENCY|BANKRUPTCY|CHAPTER[_ ]?11|LIQUIDATION|LIQUIDITY|BAILOUT|LEVERAGE|COLLATERAL|CREDIT[_ ]?RATING|RATING[_ ]?DOWNGRADE|\bCDS\b|FINANCIAL[_ ]?RISK|CREDIT[_ ]?RISK|CAPITAL[_ ]?REQUIREMENT'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(JPMORGAN|JP MORGAN|GOLDMAN SACHS|MORGAN STANLEY|BANK OF AMERICA|CITIGROUP|CITI|WELLS FARGO|HSBC|BARCLAYS|DEUTSCHE BANK|UBS|CREDIT SUISSE|MOODY.?S|S&P GLOBAL|FITCH)\b'
        )
      ) AS is_credit_banking,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'STOCK[_ ]?MARKET|STOCK[_ ]?EXCHANGE|EQUITY|EQUITIES|SHARE|SHARES|WALL[_ ]?STREET|NYSE|NASDAQ|DOW[_ ]?JONES|S[_& ]?P|SP500|S&P500|RUSSELL|INDEX|MARKET[_ ]?RALLY|SELL[_ ]?OFF|CORRECTION|VOLATILITY|\bVIX\b|EARNINGS|GUIDANCE|PROFIT[_ ]?WARNING|DIVIDEND|SHARE[_ ]?BUYBACK|IPO|SPAC|MERGER|ACQUISITION|M_AND_A|TAKEOVER|ETF|FUND|HEDGE[_ ]?FUND'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(NYSE|NASDAQ|S&P|MSCI|FTSE|BLACKROCK|VANGUARD|STATE STREET|BERKSHIRE|ARK INVEST)\b'
        )
      ) AS is_equity_market,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'CRYPTOCURRENCY|CRYPTO\b|BITCOIN|\bBTC\b|ETHEREUM|\bETH\b|BLOCKCHAIN|DIGITAL[_ ]?ASSET|DIGITAL[_ ]?ASSETS|DIGITAL[_ ]?CURRENCY|VIRTUAL[_ ]?CURRENCY|STABLECOIN|STABLECOINS|DEFI|DECENTRALIZED[_ ]?FINANCE|WEB3|ALTCOIN|TOKEN|NFT|SMART[_ ]?CONTRACT|CRYPTO[_ ]?EXCHANGE|SPOT[_ ]?ETF'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(BITCOIN|ETHEREUM|BINANCE|COINBASE|TETHER|RIPPLE|FTX|KRAKEN|GRAYSCALE|MICROSTRATEGY|BITWISE)\b'
        )
      ) AS is_crypto,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'COMMODIT|ENERGY|\bOIL\b|_OIL|OIL_|CRUDE|CRUDE[_ ]?OIL|PETROLEUM|BRENT|WTI|FUEL|DIESEL|GASOLINE|REFINERY|PIPELINE|NATURAL[_ ]?GAS|NATURALGAS|\bLNG\b|COAL|ELECTRICITY|POWER[_ ]?GRID|NUCLEAR[_ ]?ENERGY|OPEC|GOLD|SILVER|COPPER|LITHIUM|URANIUM|PALLADIUM|PLATINUM|IRON[_ ]?ORE|STEEL|RARE[_ ]?EARTH|RARE[_ ]?EARTHS|MINERAL|MINING|AGRICULTURAL[_ ]?COMMODITY|WHEAT|CORN|SOYBEAN|SOYBEANS|COFFEE|COCOA|SUGAR|SOLAR|WIND[_ ]?POWER|RENEWABLE'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(OPEC|ARAMCO|EXXON|CHEVRON|SHELL|BP|TOTALENERGIES|GAZPROM|ROSNEFT|TRANSNEFT|BHP|RIO TINTO|VALE|GLENCORE)\b'
        )
      ) AS is_commodity_energy,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'TRADE[_ ]?DISPUTE|TRADE[_ ]?WAR|TARIFF|SANCTION|SANCTIONS|EMBARGO|EXPORT[_ ]?CONTROL|EXPORT[_ ]?CONTROLS|EXPORT|IMPORT|IMPORT[_ ]?RESTRICTION|TRADE[_ ]?RESTRICTION|SUPPLY[_ ]?CHAIN|SUPPLYCHAIN|LOGISTICS|SHIPPING|CONTAINER|FREIGHT|CARGO|CUSTOMS|PORT|PORTS|MARITIME|CANAL|SUEZ|PANAMA[_ ]?CANAL|RED[_ ]?SEA|STRAIT|HORMUZ|BAB[_ ]?EL[_ ]?MANDEB|BLACK[_ ]?SEA|RAIL|TRUCKING|AIR[_ ]?FREIGHT|WAREHOUSE|INVENTORY'
        )
        OR REGEXP_CONTAINS(
          loc_u,
          r'RED SEA|SUEZ|PANAMA CANAL|HORMUZ|BLACK SEA'
        )
      ) AS is_trade_supply,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'REAL[_ ]?ESTATE|REALESTATE|PROPERTY|HOUSING|HOME[_ ]?BUILD|HOMEBUILD|MORTGAGE|COMMERCIAL[_ ]?REAL[_ ]?ESTATE|COMMERCIAL[_ ]?PROPERTY|OFFICE[_ ]?PROPERTY|RENT|RENTAL|URBAN|INFRASTRUCTURE|CONSTRUCTION|BUILDING|BRIDGE|ROAD|RAIL|AIRPORT|METRO|\bREIT\b|PUBLIC[_ ]?WORKS'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(EVERGRANDE|COUNTRY GARDEN|VANKE|BLACKSTONE|BROOKFIELD|PROLOGIS|CBRE|JLL|ZILLOW)\b'
        )
      ) AS is_real_estate_infra,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'TECH|TECHNOLOGY|ARTIFICIAL[_ ]?INTELLIGENCE|\bAI\b|GENERATIVE[_ ]?AI|FRONTIER[_ ]?MODEL|FOUNDATION[_ ]?MODEL|\bLLM\b|MACHINE[_ ]?LEARNING|ROBOTICS|AUTONOMOUS|SOFTWARE|HARDWARE|SEMICONDUCTOR|SEMICONDUCTORS|CHIP|CHIPS|ADVANCED[_ ]?CHIPS|\bGPU\b|DATA[_ ]?CENTER|DATACENTER|CLOUD|CYBER[_ ]?SECURITY|CYBERSECURITY|CYBER[_ ]?ATTACK|HACKER|HACKING|MALWARE|PHISHING|RANSOMWARE|DATA[_ ]?BREACH|DIGITAL|PLATFORM|TELECOM|5G|QUANTUM|EXPORT[_ ]?CONTROLS'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(OPENAI|NVIDIA|TSMC|ASML|AMD|INTEL|MICROSOFT|GOOGLE|ALPHABET|META|AMAZON|APPLE|TESLA|BROADCOM|ARM|QUALCOMM|ORACLE|CISCO|PALANTIR)\b'
        )
      ) AS is_tech_ai_chip,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'BUSINESS|COMPANY|CORPORATE|INDUSTRY|INDUSTRIAL|MANUFACTURING|FACTORY|FACTORY[_ ]?ORDERS|DURABLE[_ ]?GOODS|PRODUCTION|CAPEX|INVENTORY|WHOLESALE|RETAIL|RETAIL[_ ]?SALES|CONSUMER|CONSUMER[_ ]?CONFIDENCE|SALES|REVENUE|PROFIT|MARGIN|EARNINGS[_ ]?GUIDANCE|LAYOFF|LAYOFFS|JOB[_ ]?CUTS|UNEMPLOYMENT|JOB[_ ]?MARKET|PAYROLL|\bNFP\b|WAGE|WAGES|WAGE[_ ]?GROWTH|\bPMI\b|\bISM\b|AUTO|EV|AIRLINE|TOURISM|HOTEL|RESTAURANT'
        )
      ) AS is_real_economy,
      (
        REGEXP_CONTAINS(
          theme_u,
          r'LAW\b|LEGAL|LEGISLATION|REGULATION|REGULATORY|ANTITRUST|LAWSUIT|LITIGATION|COURT|JUDGE|TRIAL|SUBPOENA|INDICTMENT|PROSECUT|INVESTIGATION|SEIZURE|SETTLEMENT|FINE|PENALTY|COMPLIANCE|FRAUD|CORRUPTION|MONEY[_ ]?LAUNDERING|SANCTION|SANCTIONS|EXPORT[_ ]?BAN'
        )
        OR REGEXP_CONTAINS(
          org_u,
          r'\b(SEC|CFTC|DOJ|FCA|ESMA|FINRA|FTC|SUPREME COURT|EUROPEAN COMMISSION)\b'
        )
      ) AS is_legal_regulatory,
      (
        EventRootCode IN ('18', '19', '20', '14')
        OR REGEXP_CONTAINS(
          theme_u,
          r'WAR|CONFLICT|MILITARY|MISSILE|DRONE|ATTACK|TERROR|TERRORISM|CRISIS|COUP|UNREST|PROTEST|RIOT|BORDER|INVASION|ESCALATION|CEASEFIRE|NATO|DEFENSE|SECURITY'
        )
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
      ARRAY(
        SELECT asset
        FROM UNNEST(ARRAY_CONCAT(
          IF(is_equity_market OR is_real_economy OR is_tech_ai_chip, ['stocks'], []),
          IF(is_macro OR is_credit_banking, ['bonds'], []),
          IF(
            REGEXP_CONTAINS(theme_u, r'DOLLAR|\bUSD\b|FOREIGN[_ ]?EXCHANGE|\bFX\b|CURRENCY[_ ]?RESERVE|ECON_WORLDCURRENCIES'),
            ['USD'],
            []
          ),
          IF(
            REGEXP_CONTAINS(theme_u, r'GOLD|SILVER|PRECIOUS'),
            ['gold'],
            []
          ),
          IF(
            REGEXP_CONTAINS(theme_u, r'\bOIL\b|CRUDE|BRENT|WTI|PETROLEUM|OPEC'),
            ['oil'],
            []
          ),
          IF(
            REGEXP_CONTAINS(theme_u, r'NATURAL[_ ]?GAS|NATURALGAS|\bLNG\b'),
            ['gas'],
            []
          ),
          IF(is_crypto, ['crypto'], []),
          IF(is_credit_banking, ['banks'], []),
          IF(is_real_estate_infra, ['real_estate'], [])
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
  REGEXP_REPLACE(COALESCE(V2Organizations, ''), r',?\d+', '') AS Cac_To_Chuc_Lien_Quan,
  V2Themes,
  V2Persons,
  V2Locations
FROM FinalClassified
WHERE primary_sector != 'Khác'
ORDER BY
  So_Bao_De_Cap DESC,
  ABS(Diem_Cam_Xuc) DESC,
  source_count DESC
LIMIT 100
