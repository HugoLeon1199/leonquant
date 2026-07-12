#!/usr/bin/env python3
"""Offline-first tests for the standalone tech pipeline."""

from __future__ import annotations

import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_tech_publication import build_publication  # noqa: E402
from scripts.run_tech_gdelt import companies_from_blob  # noqa: E402
from scripts.tech_common import PASS_STATUSES, TECH_PUBLICATION_SCHEMA, TECH_SOURCE_COVERAGE_MATRIX, TECH_WATCHLIST_CONFIGURED_SOURCES  # noqa: E402
from scripts.validate_tech_publication import validate as validate_publication  # noqa: E402
from tech.acquire_api_sources import arxiv_entry_candidate, candidate as api_candidate, github_release_candidate, github_repo_candidate, hf_model_candidate  # noqa: E402

FORBIDDEN_DIFF_PATHS = {
    "config/sources_seed.txt",
    "leon.py",
    "summarize_news_gemini.py",
    "build_website_content.py",
    "sql/gdelt_invest_pulse.sql",
    ".github/workflows/daily.yml",
    ".github/workflows/pulse-hourly.yml",
}


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_validation_fixture_generation() -> None:
    sources = [
        {
            "name": "Pass RSS",
            "input_url": "https://example.com/rss",
            "domain": "example.com",
            "validation_status": "PASS_RSS",
        },
        {
            "name": "Soft Pass",
            "input_url": "https://soft.example.com",
            "domain": "soft.example.com",
            "validation_status": "SOFT_PASS",
        },
    ]
    active = sum(1 for src in sources if src["validation_status"] in PASS_STATUSES)
    disabled = len(sources) - active
    assert_true(active == 1, "fixture active count mismatch")
    assert_true(disabled == 1, "fixture disabled count mismatch")


def test_gdelt_companies_from_blob_expanded_entities() -> None:
    blob = (
        "Z.ai 智谱 BigModel Qwen Kimi Moonshot MiniMax Doubao Hunyuan "
        "Flux ComfyUI Stable Diffusion LoRA ControlNet Kling Veo HunyuanVideo "
        "OpenRouter Replicate fal.ai SGLang MCP LangGraph"
    )
    tags = set(companies_from_blob(blob))
    expected = {
        "Z.ai", "Zhipu", "BigModel", "Qwen", "Kimi", "Moonshot", "MiniMax",
        "Doubao", "Hunyuan", "Flux", "ComfyUI", "Stable Diffusion", "LoRA",
        "ControlNet", "Kling", "Veo", "HunyuanVideo", "OpenRouter",
        "Replicate", "fal.ai", "SGLang", "MCP", "LangGraph",
    }
    missing = sorted(expected - tags)
    assert_true(not missing, f"companies_from_blob missing expanded entities: {missing}")


def test_api_acquisition_candidate_fixtures() -> None:
    aliases = [
        {"entity": "Qwen/Alibaba", "alias": "Qwen"},
        {"entity": "DeepSeek", "alias": "DeepSeek"},
        {"entity": "Flux/Black Forest Labs", "alias": "Flux"},
        {"entity": "ComfyUI", "alias": "ComfyUI"},
        {"entity": "LangGraph", "alias": "LangGraph"},
        {"entity": "OpenHands", "alias": "OpenHands"},
        {"entity": "Zhipu/Z.ai", "alias": "GLM-5.2"},
    ]
    hf_qwen = hf_model_candidate(
        {"modelId": "Qwen/Qwen3-Coder", "lastModified": "2026-07-10T00:00:00Z", "tags": ["text-generation"], "pipeline_tag": "text-generation"},
        "Qwen",
        aliases,
    )
    hf_deepseek = hf_model_candidate(
        {"modelId": "deepseek-ai/DeepSeek-R1", "lastModified": "2026-07-10T00:00:00Z", "tags": ["reasoning"], "pipeline_tag": "text-generation"},
        "DeepSeek",
        aliases,
    )
    hf_flux = hf_model_candidate(
        {"modelId": "black-forest-labs/FLUX.2", "lastModified": "2026-07-10T00:00:00Z", "tags": ["image-generation"], "pipeline_tag": "text-to-image"},
        "Flux",
        aliases,
    )
    for item in (hf_qwen, hf_deepseek, hf_flux):
        assert_true(item is not None, "HF fixture should create candidate")
        assert_true(item["source_lane"] == "huggingface_model", "HF candidate lane mismatch")
        assert_true(item["content_quality"] == "metadata_only", "HF should keep metadata-only candidate")
        assert_true(item["raw_source_method"] == "hf_api", "HF raw method mismatch")
        assert_true(item["match_strength"] in {"strong", "medium"}, "official HF fixtures should not be weak")
        assert_true(item["is_test_repo"] is False, "official HF fixtures should not be test repos")

    gh_comfy = github_release_candidate(
        "comfyanonymous/ComfyUI",
        {"name": "ComfyUI v1", "html_url": "https://github.com/comfyanonymous/ComfyUI/releases/tag/v1", "published_at": "2026-07-10T00:00:00Z", "body": "ComfyUI workflow release."},
        aliases,
    )
    gh_langgraph = github_release_candidate(
        "langchain-ai/langgraph",
        {"name": "LangGraph v1", "html_url": "https://github.com/langchain-ai/langgraph/releases/tag/v1", "published_at": "2026-07-10T00:00:00Z", "body": "LangGraph agents release."},
        aliases,
    )
    gh_openhands = github_release_candidate(
        "All-Hands-AI/OpenHands",
        {"name": "OpenHands v1", "html_url": "https://github.com/All-Hands-AI/OpenHands/releases/tag/v1", "published_at": "2026-07-10T00:00:00Z", "body": "OpenHands coding agent release."},
        aliases,
    )
    for item in (gh_comfy, gh_langgraph, gh_openhands):
        assert_true(item is not None, "GitHub fixture should create candidate")
        assert_true(item["source_lane"] == "github_release", "GitHub candidate lane mismatch")
        assert_true(item["raw_source_method"] == "github_api", "GitHub raw method mismatch")

    hf_personal_test = hf_model_candidate(
        {"modelId": "KimiTool/MyAwesomeModel-TestRepo", "lastModified": "2026-07-10T00:00:00Z", "tags": ["text-generation", "base_model:moonshotai/Kimi"], "pipeline_tag": "text-generation"},
        "Kimi",
        [{"entity": "Kimi/Moonshot", "alias": "Kimi"}],
    )
    assert_true(hf_personal_test is not None, "HF personal test repo fixture should be classified")
    assert_true(hf_personal_test["is_test_repo"] is True, "HF personal test repo should be marked test")
    assert_true(hf_personal_test["match_strength"] == "weak", "HF personal test repo should be weak confidence")
    assert_true(hf_personal_test["evidence"] == "weak_metadata_match", "HF personal test repo should use weak evidence")

    hf_zai = hf_model_candidate(
        {"modelId": "zai-org/GLM-5.2", "lastModified": "2026-07-10T00:00:00Z", "tags": ["text-generation"], "pipeline_tag": "text-generation"},
        "GLM-5.2",
        aliases,
    )
    assert_true(hf_zai is not None, "HF official Z.ai GLM-5.2 should be kept")
    assert_true(hf_zai["matched_entity"] == "Zhipu/Z.ai", "HF official GLM should match Zhipu/Z.ai")
    assert_true(hf_zai["official_entity_source"] is True, "HF official GLM should mark official org")
    assert_true(hf_zai["match_strength"] in {"strong", "medium"}, "HF official GLM should not be weak")

    deepseek_with_qwen_tag = hf_model_candidate(
        {"modelId": "deepseek-ai/DeepSeek-R2", "lastModified": "2026-07-10T00:00:00Z", "tags": ["base_model:Qwen/Qwen3"], "pipeline_tag": "text-generation", "cardData": {"base_model": "Qwen/Qwen3"}},
        "Qwen",
        [{"entity": "Qwen/Alibaba", "alias": "Qwen"}, {"entity": "DeepSeek", "alias": "DeepSeek"}],
    )
    assert_true(deepseek_with_qwen_tag is not None, "DeepSeek fixture should create candidate")
    assert_true(deepseek_with_qwen_tag["matched_entity"] == "DeepSeek", "DeepSeek repo must not be matched as Qwen from base_model tag")

    atom = """<entry xmlns="http://www.w3.org/2005/Atom">
      <title>Reasoning model agents for multimodal tool use</title>
      <id>http://arxiv.org/abs/2607.00001v1</id>
      <published>2026-07-10T00:00:00Z</published>
      <summary>We study LLM agents, MCP tool use and multimodal reasoning models.</summary>
      <author><name>A. Researcher</name></author>
      <link href="https://arxiv.org/abs/2607.00001" rel="alternate" />
    </entry>"""
    import xml.etree.ElementTree as ET
    arxiv_item = arxiv_entry_candidate(ET.fromstring(atom), aliases)
    assert_true(arxiv_item is not None, "arXiv fixture should create candidate")
    assert_true(arxiv_item["source_lane"] == "research_papers", "arXiv lane mismatch")
    assert_true(arxiv_item["content_quality"] == "summary_only", "arXiv summary candidate should be kept")

    rss_item = api_candidate(
        title="RSS item from official source",
        url="https://example.com/rss-item",
        source="example.com",
        source_lane="official_ai_labs",
        summary="RSS summary only.",
        published_at="2026-07-10T00:00:00Z",
        raw_source_method="rss",
        content_quality="summary_only",
        evidence="rss_fixture",
    )
    sitemap_item = api_candidate(
        title="Sitemap metadata item",
        url="https://example.com/sitemap-item",
        source="example.com",
        source_lane="independent_ai_news",
        summary="Sitemap metadata only.",
        published_at="2026-07-10T00:00:00Z",
        raw_source_method="sitemap",
        content_quality="metadata_only",
        evidence="sitemap_fixture",
    )
    assert_true(rss_item is not None and rss_item["raw_source_method"] == "rss", "RSS fixture candidate missing")
    assert_true(sitemap_item is not None and sitemap_item["content_quality"] == "metadata_only", "metadata-only sitemap should be kept")


def test_publication_build_and_validate() -> None:
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ["LEON_TECH_OFFLINE_TEST"] = "1"
    now = datetime.now(timezone.utc).isoformat()
    crawl = {
        "articles": [
            {
                "title": "OpenAI launches new coding model",
                "url": "https://example.com/openai-coding-model",
                "text": "OpenAI launches a new coding model for developer workflows and agent tooling." * 20,
                "published_at": now,
                "source": "example.com",
            },
            {
                "title": "Anthropic releases agent workflow SDK",
                "url": "https://another.com/openai-coding-model",
                "text": "Anthropic releases an agent workflow SDK with model context protocol support and automation examples." * 20,
                "published_at": now,
                "source": "another.com",
            },
            {
                "title": "Qwen adds local multimodal model tools",
                "url": "https://qbitai.com/qwen-local-model",
                "text": "Qwen adds local multimodal model tools for private AI workflows and developer experiments." * 20,
                "published_at": now,
                "source": "qbitai.com",
            },
            {
                "title": "GitHub trending repo adds MCP automation demo",
                "url": "https://github.com/example/mcp-demo",
                "text": "A GitHub repository adds an MCP automation demo with agent tool use and practical developer workflow examples." * 20,
                "published_at": now,
                "source": "github.com",
            },
            {
                "title": "NVIDIA GPU inference toolkit update",
                "url": "https://developer.nvidia.com/blog/gpu-inference-toolkit",
                "text": "NVIDIA updates a GPU inference toolkit for AI model serving, automation and developer deployment." * 20,
                "published_at": now,
                "source": "developer.nvidia.com",
            },
        ]
    }
    gdelt = {
        "raw_event_count": 1,
        "ai_filtered_event_count": 1,
        "rejected_non_ai_count": 0,
        "bytes_status": "known",
        "events": [
            {
                "event_id": "123",
                "title": "NVIDIA expands GPU data center roadmap",
                "summary": "GPU, HBM and cloud server capacity stay at the center of AI infrastructure demand.",
                "source_urls": ["https://infra.example.com/nvidia", "https://market.example.com/nvidia"],
                "source_count": 2,
                "independent_domain_count": 2,
                "official_source_present": False,
                "topic_tags": ["chip_ha_tang"],
                "reported_at": now,
                "freshness_hours": 72,
            }
        ]
    }
    publication = build_publication(crawl, gdelt)
    assert_true(publication["schema_version"] == TECH_PUBLICATION_SCHEMA, "schema mismatch")
    assert_true(publication["window_hours"] == 72, "window_hours mismatch")
    assert_true(len(publication["must_read"]) >= 5, "must_read floor not enforced")
    errs = validate_publication(publication, check_external=False)
    assert_true(not errs, f"publication validation errors: {errs}")
    matrix = TECH_SOURCE_COVERAGE_MATRIX.read_text(encoding="utf-8")
    assert_true("active_url_sources:" in matrix, "coverage matrix must report active_url_sources")
    assert_true("active_watchlist_entities:" in matrix, "coverage matrix must report active_watchlist_entities")
    assert_true("real_candidate_count:" in matrix, "coverage matrix must report real_candidate_count")
    assert_true("manual_signal_count:" in matrix, "coverage matrix must report manual_signal_count")
    assert_true("weak_metadata_match_count:" in matrix, "coverage matrix must report weak_metadata_match_count")
    assert_true("| official_ai_labs | 26 | 26 |" not in matrix, "coverage matrix must not present watchlist entities as active URL sources")
    assert_true("watchlist entities are not URL crawl sources" in matrix, "coverage matrix should explain watchlist/entity distinction")


def test_watchlist_configured_sources_are_debug_only() -> None:
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ["LEON_TECH_OFFLINE_TEST"] = "1"
    os.environ["LEON_TECH_DISABLE_API_CANDIDATES"] = "1"
    try:
        publication = build_publication({"articles": []}, {"events": []})
    finally:
        os.environ.pop("LEON_TECH_DISABLE_API_CANDIDATES", None)
    assert_true(publication["stats"]["candidate_count"] == 0, "configured watchlist URLs must not create publication candidates")
    assert_true(publication["stats"]["manual_signal_count"] == 0, "manual_signal must not be in candidate pool")
    assert_true(not publication["sections"]["full_link_radar"], "manual watchlist URLs must not enter Full Radar")
    assert_true(TECH_WATCHLIST_CONFIGURED_SOURCES.is_file(), "watchlist configured sources debug artifact missing")


def test_manual_signal_validator_guard() -> None:
    now = datetime.now(timezone.utc).isoformat()
    publication = {
        "schema_version": TECH_PUBLICATION_SCHEMA,
        "window_hours": 72,
        "executive_summary": ["Trong 72 giờ qua, radar có tín hiệu AI mới cần kiểm tra."],
        "top_signal_clusters": [
            {
                "cluster_id": "cluster-01",
                "cluster_title": "Configured source should not publish",
                "takeaway": "Tín hiệu cấu hình không được xuất bản như tin mới.",
                "what_changed": "Không có fetched item thật.",
                "why_it_matters": "Tránh bơm nguồn configured vào radar.",
                "affected_ecosystem": ["model providers"],
                "entities": ["Zhipu/Z.ai"],
                "links": [
                    {
                        "title": "Configured source",
                        "url": "https://z.ai/blog",
                        "source": "z.ai",
                        "source_lane": "huggingface_model",
                        "content_quality": "metadata_only",
                        "raw_source_method": "manual_signal",
                        "evidence": "watchlist_configured_source",
                        "published_at": now,
                    }
                ],
            }
        ],
        "must_read": [
            {
                "title": "Configured source",
                "url": "https://z.ai/blog",
                "source": "z.ai",
                "category": "model",
                "importance": 3,
                "why_read": "Nguồn cấu hình không phải bài mới thật.",
                "apply_now": "Không dùng làm Must Read.",
                "tags": ["ai_models", "official"],
                "source_count": 1,
                "source_type": "official",
                "published_at": now,
                "curation_status": "fallback",
                "signal_type": "new_release",
                "confidence": "medium",
                "evidence": "watchlist_configured_source",
                "time_to_apply": "this_week",
                "leon_fit": "Chỉ là kiểm thử validator.",
                "source_lane": "huggingface_model",
                "content_quality": "metadata_only",
                "raw_source_method": "manual_signal",
            }
        ],
        "sections": {
            "ai_models": [],
            "local_ai_china_ai": [],
            "ai_tools": [],
            "automation_mcp_agents": [],
            "open_source_hot": [],
            "ai_business_money": [],
            "industry_impact": [],
            "ai_knowledge": [{"concept": "Manual signal guard", "explain_simple": "Không xuất bản nguồn cấu hình.", "why_now": "Cần chặn lỗi nguồn.", "how_to_apply": "Dùng validator.", "best_links": ["https://z.ai/blog"]}],
            "founder_ideas_for_leon": [{"idea": "Không dùng manual source", "based_on": "Configured source", "why_now": "Giữ chất lượng nguồn.", "apply_now": "Chặn bằng validator."}],
            "full_link_radar": [
                {
                    "title": "Configured source",
                    "url": "https://z.ai/blog",
                    "category": "model",
                    "source_lane": "huggingface_model",
                    "content_quality": "metadata_only",
                    "raw_source_method": "manual_signal",
                    "one_line_reason": "Nguồn cấu hình.",
                    "why_interesting": "Không phải fetched item.",
                    "use_case": "Không dùng.",
                    "source_type": "official",
                }
            ],
        },
        "stats": {"curator_candidate_count": 1, "main_candidate_count": 1, "candidate_count": 1, "manual_signal_count": 1, "manual_signal_share": 1.0, "render_checks": {"knowledge_fields_ready": True, "founder_fields_ready": True}},
    }
    errs = validate_publication(publication, check_external=False)
    assert_true(any("must_read[0] manual_signal" in err for err in errs), "validator should reject manual_signal in Must Read")
    assert_true(any("top_signal_clusters[0].links[0] manual_signal" in err for err in errs), "validator should reject manual_signal in Top Signal links")
    assert_true(any("manual_signal share" in err for err in errs), "validator should reject manual_signal share above threshold")


def test_frontier_watchlist_glm_5_2_fixture() -> None:
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ["LEON_TECH_OFFLINE_TEST"] = "1"
    now = datetime.now(timezone.utc).isoformat()
    crawl = {
        "articles": [
            {
                "title": "Z.ai introduces GLM-5.2 for long-horizon coding tasks",
                "url": "https://z.ai/blog/glm-5.2",
                "text": "Z.ai, also known as Zhipu AI, introduces GLM-5.2 with long-horizon coding and agentic engineering capabilities." * 16,
                "published_at": now,
                "source": "z.ai",
            },
            {
                "title": "Zhipu GLM-5.2 developer documentation updated",
                "url": "https://docs.z.ai/guides/llm/glm-5.2",
                "text": "The Z.ai developer documentation describes GLM-5.2 model positioning, long context and coding workflows." * 16,
                "published_at": now,
                "source": "docs.z.ai",
            },
            {
                "title": "GLM-5.2 model card appears under zai-org",
                "url": "https://huggingface.co/zai-org/GLM-5.2",
                "text": "The Hugging Face model page for zai-org GLM-5.2 references Zhipu AI, model weights and developer usage." * 16,
                "published_at": now,
                "source": "huggingface.co",
            },
            {
                "title": "DeepMind releases model research notes",
                "url": "https://deepmind.google/blog/model-research-notes",
                "text": "DeepMind publishes model research notes about AI agents, evaluation, reasoning and developer workflows." * 16,
                "published_at": now,
                "source": "deepmind.google",
            },
            {
                "title": "Mistral AI updates developer model platform",
                "url": "https://mistral.ai/news/developer-model-platform",
                "text": "Mistral AI updates its developer platform for model deployment, tooling, inference and enterprise workflows." * 16,
                "published_at": now,
                "source": "mistral.ai",
            },
        ]
    }
    publication = build_publication(crawl, {"events": []})
    stats = publication["stats"]
    assert_true(stats["watchlist_entity_count"] >= 10, "frontier watchlist entity count missing")
    assert_true(stats["watchlist_candidate_count"] >= 3, "GLM watchlist candidates not detected")
    assert_true(stats["glm_5_2_detected"] is True, "GLM-5.2 should be detected")

    main_items = []
    for section_name in ("ai_models", "local_ai_china_ai"):
        main_items.extend(publication["sections"].get(section_name) or [])
    glm_items = [
        item for item in main_items
        if item.get("matched_entity") == "Zhipu/Z.ai" and str(item.get("matched_alias") or "").lower() in {"z.ai", "zhipu ai", "glm-5.2", "glm"}
    ]
    assert_true(glm_items, "GLM-5.2 must appear in model/local_ai main section")
    assert_true(glm_items[0]["category"] in {"model", "local_ai"}, "GLM-5.2 category must be model/local_ai")
    assert_true(glm_items[0]["source_type"] in {"official", "independent"}, "GLM official/independent source expected")

    must_read = publication["must_read"]
    assert_true(any(item.get("matched_entity") == "Zhipu/Z.ai" for item in must_read), "GLM-5.2 should be considered for Must Read")
    errs = validate_publication(publication, check_external=False)
    assert_true(not errs, f"GLM fixture validation errors: {errs}")


def test_multilane_frontier_fixtures_clustered() -> None:
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ["LEON_TECH_OFFLINE_TEST"] = "1"
    now = datetime.now(timezone.utc).isoformat()
    crawl = {
        "articles": [
            {
                "title": "Black Forest Labs updates FLUX image model workflow",
                "url": "https://huggingface.co/black-forest-labs/FLUX.2",
                "text": "Flux and Black Forest Labs publish model card details for image generation workflows and inference." * 16,
                "published_at": now,
                "source": "huggingface.co",
            },
            {
                "title": "ComfyUI node release improves video workflow routing",
                "url": "https://github.com/comfyanonymous/ComfyUI/releases/tag/v1.0",
                "text": "ComfyUI releases a node and workflow update for image video automation and graph execution." * 16,
                "published_at": now,
                "source": "github.com",
            },
            {
                "title": "Runway and Kling video model tools gain new production options",
                "url": "https://runwayml.com/research/video-model-update",
                "text": "Runway and Kling style video AI workflows add production controls for creative teams and model evaluation." * 16,
                "published_at": now,
                "source": "runwayml.com",
            },
            {
                "title": "OpenRouter lists new frontier model routing options",
                "url": "https://openrouter.ai/models",
                "text": "OpenRouter model listings show new routing options for frontier LLMs and developer applications." * 16,
                "published_at": now,
                "source": "openrouter.ai",
            },
            {
                "title": "MCP LangGraph LlamaIndex agent stack release",
                "url": "https://github.com/modelcontextprotocol/servers/releases/tag/test",
                "text": "MCP, LangGraph and LlamaIndex agent tooling updates connect models, tools, data and workflow automation." * 16,
                "published_at": now,
                "source": "github.com",
            },
            {
                "title": "Cursor Claude Code and OpenHands coding agents update",
                "url": "https://www.cursor.com/changelog",
                "text": "Cursor, Claude Code and OpenHands signal faster coding agent workflows and repository automation." * 16,
                "published_at": now,
                "source": "cursor.com",
            },
        ]
    }
    publication = build_publication(crawl, {"events": []})
    stats = publication["stats"]
    lanes = stats.get("candidates_by_lane") or {}
    assert_true(stats["model_hub_candidate_count"] > 0, "model hub lane should produce candidates")
    assert_true(stats["image_video_workflow_candidate_count"] > 0, "image/video lane should produce candidates")
    assert_true(int(lanes.get("github_release") or 0) > 0, "GitHub release lane should produce candidates")
    assert_true(int(lanes.get("huggingface_model") or 0) > 0, "Hugging Face lane should produce candidates")
    assert_true(publication.get("top_signal_clusters"), "top signal clusters should be built")
    cluster_entities = [
        entity
        for cluster in publication["top_signal_clusters"]
        for entity in (cluster.get("entities") or [])
    ]
    assert_true(any("Flux" in entity or "Black Forest" in entity for entity in cluster_entities), "Flux/BFL should be clustered")
    assert_true(any("ComfyUI" in entity for entity in cluster_entities), "ComfyUI should be clustered")
    entity_counts = {entity: cluster_entities.count(entity) for entity in set(cluster_entities)}
    assert_true(all(count < 3 for count in entity_counts.values()), "Top Signals should not split one entity into 3+ clusters")
    full_radar = publication["sections"]["full_link_radar"]
    assert_true(any(item.get("source_lane") == "huggingface_model" for item in full_radar), "Full Radar should keep HF link")
    assert_true(any(item.get("source_lane") == "github_release" for item in full_radar), "Full Radar should keep GitHub link")
    errs = validate_publication(publication, check_external=False)
    assert_true(not errs, f"multilane fixture validation errors: {errs}")


def test_frontier_watchlist_glm_5_2_fixture() -> None:
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ["LEON_TECH_OFFLINE_TEST"] = "1"
    now = datetime.now(timezone.utc).isoformat()
    crawl = {
        "articles": [
            {
                "title": "Z.ai introduces GLM-5.2 for long-horizon coding tasks",
                "url": "https://z.ai/blog/glm-5.2",
                "text": "Z.ai, also known as Zhipu AI, introduces GLM-5.2 with long-horizon coding and agentic engineering capabilities." * 16,
                "published_at": now,
                "source": "z.ai",
            },
            {
                "title": "Zhipu GLM-5.2 developer documentation updated",
                "url": "https://docs.z.ai/guides/llm/glm-5.2",
                "text": "The Z.ai developer documentation describes GLM-5.2 model positioning, long context and coding workflows." * 16,
                "published_at": now,
                "source": "docs.z.ai",
            },
            {
                "title": "GLM-5.2 model card appears under zai-org",
                "url": "https://huggingface.co/zai-org/GLM-5.2",
                "text": "The Hugging Face model page for zai-org GLM-5.2 references Zhipu AI, model weights and developer usage." * 16,
                "published_at": now,
                "source": "huggingface.co",
            },
            {
                "title": "DeepMind releases model research notes",
                "url": "https://deepmind.google/blog/model-research-notes",
                "text": "DeepMind publishes model research notes about AI agents, evaluation, reasoning and developer workflows." * 16,
                "published_at": now,
                "source": "deepmind.google",
            },
            {
                "title": "Mistral AI updates developer model platform",
                "url": "https://mistral.ai/news/developer-model-platform",
                "text": "Mistral AI updates its developer platform for model deployment, tooling, inference and enterprise workflows." * 16,
                "published_at": now,
                "source": "mistral.ai",
            },
        ]
    }
    publication = build_publication(crawl, {"events": []})
    stats = publication["stats"]
    assert_true(stats["watchlist_entity_count"] >= 10, "frontier watchlist entity count missing")
    assert_true(stats["watchlist_candidate_count"] >= 3, "GLM watchlist candidates not detected")
    assert_true(stats["glm_5_2_detected"] is True, "GLM-5.2 should be detected")

    main_items = []
    for section_name in ("ai_models", "local_ai_china_ai"):
        main_items.extend(publication["sections"].get(section_name) or [])
    glm_items = [
        item for item in main_items
        if item.get("matched_entity") == "Zhipu/Z.ai" and str(item.get("matched_alias") or "").lower() in {"z.ai", "zhipu ai", "glm-5.2", "glm"}
    ]
    assert_true(glm_items, "GLM-5.2 must appear in model/local_ai main section")
    assert_true(glm_items[0]["category"] in {"model", "local_ai"}, "GLM-5.2 category must be model/local_ai")
    assert_true(glm_items[0]["source_type"] in {"official", "independent"}, "GLM official/independent source expected")

    must_read = publication["must_read"]
    assert_true(any(item.get("matched_entity") == "Zhipu/Z.ai" for item in must_read), "GLM-5.2 should be considered for Must Read")
    errs = validate_publication(publication, check_external=False)
    assert_true(not errs, f"GLM fixture validation errors: {errs}")


def test_multilane_frontier_fixtures_clustered() -> None:
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ["LEON_TECH_OFFLINE_TEST"] = "1"
    now = datetime.now(timezone.utc).isoformat()
    crawl = {
        "articles": [
            {
                "title": "Black Forest Labs updates FLUX image model workflow",
                "url": "https://huggingface.co/black-forest-labs/FLUX.2",
                "text": "Flux and Black Forest Labs publish model card details for image generation workflows and inference." * 16,
                "published_at": now,
                "source": "huggingface.co",
            },
            {
                "title": "ComfyUI node release improves video workflow routing",
                "url": "https://github.com/comfyanonymous/ComfyUI/releases/tag/v1.0",
                "text": "ComfyUI releases a node and workflow update for image video automation and graph execution." * 16,
                "published_at": now,
                "source": "github.com",
            },
            {
                "title": "Runway and Kling video model tools gain new production options",
                "url": "https://runwayml.com/research/video-model-update",
                "text": "Runway and Kling style video AI workflows add production controls for creative teams and model evaluation." * 16,
                "published_at": now,
                "source": "runwayml.com",
            },
            {
                "title": "OpenRouter lists new frontier model routing options",
                "url": "https://openrouter.ai/models",
                "text": "OpenRouter model listings show new routing options for frontier LLMs and developer applications." * 16,
                "published_at": now,
                "source": "openrouter.ai",
            },
            {
                "title": "MCP LangGraph LlamaIndex agent stack release",
                "url": "https://github.com/modelcontextprotocol/servers/releases/tag/test",
                "text": "MCP, LangGraph and LlamaIndex agent tooling updates connect models, tools, data and workflow automation." * 16,
                "published_at": now,
                "source": "github.com",
            },
            {
                "title": "Cursor Claude Code and OpenHands coding agents update",
                "url": "https://www.cursor.com/changelog",
                "text": "Cursor, Claude Code and OpenHands signal faster coding agent workflows and repository automation." * 16,
                "published_at": now,
                "source": "cursor.com",
            },
        ]
    }
    publication = build_publication(crawl, {"events": []})
    stats = publication["stats"]
    lanes = stats.get("candidates_by_lane") or {}
    assert_true(stats["model_hub_candidate_count"] > 0, "model hub lane should produce candidates")
    assert_true(stats["image_video_workflow_candidate_count"] > 0, "image/video lane should produce candidates")
    assert_true(int(lanes.get("github_release") or 0) > 0, "GitHub release lane should produce candidates")
    assert_true(int(lanes.get("huggingface_model") or 0) > 0, "Hugging Face lane should produce candidates")
    assert_true(publication.get("top_signal_clusters"), "top signal clusters should be built")
    cluster_entities = [
        entity
        for cluster in publication["top_signal_clusters"]
        for entity in (cluster.get("entities") or [])
    ]
    assert_true(any("Flux" in entity or "Black Forest" in entity for entity in cluster_entities), "Flux/BFL should be clustered")
    assert_true(any("ComfyUI" in entity for entity in cluster_entities), "ComfyUI should be clustered")
    entity_counts = {entity: cluster_entities.count(entity) for entity in set(cluster_entities)}
    assert_true(all(count < 3 for count in entity_counts.values()), "Top Signals should not split one entity into 3+ clusters")
    full_radar = publication["sections"]["full_link_radar"]
    assert_true(any(item.get("source_lane") == "huggingface_model" for item in full_radar), "Full Radar should keep HF link")
    assert_true(any(item.get("source_lane") == "github_release" for item in full_radar), "Full Radar should keep GitHub link")
    errs = validate_publication(publication, check_external=False)
    assert_true(not errs, f"multilane fixture validation errors: {errs}")


def test_empty_must_read_guard() -> None:
    publication = {
        "schema_version": TECH_PUBLICATION_SCHEMA,
        "window_hours": 72,
        "executive_summary": ["Trong 72 giờ qua, radar giữ lại 0 bài đáng đọc nhất."],
        "must_read": [],
        "sections": {
            "ai_models": [],
            "local_ai_china_ai": [],
            "ai_tools": [],
            "automation_mcp_agents": [],
            "open_source_hot": [],
            "ai_business_money": [],
            "industry_impact": [],
            "ai_knowledge": [],
            "founder_ideas_for_leon": [],
            "full_link_radar": [{"title": "Link AI có dấu", "url": "https://example.com/a", "category": "tool", "why_interesting": "Có tín hiệu công cụ AI mới.", "use_case": "Mở link để kiểm tra nhanh.", "source_type": "independent"}],
        },
        "stats": {"curator_candidate_count": 5, "main_candidate_count": 10, "render_checks": {"knowledge_fields_ready": True, "founder_fields_ready": True}},
    }
    errs = validate_publication(publication, check_external=False)
    assert_true(any("must_read must not be empty" in err for err in errs), "empty must_read should fail")
    assert_true(any("0 bài đáng đọc" in err for err in errs), "0 bài summary should fail")


def test_mobile_layout_smoke() -> None:
    html = (ROOT / "tech" / "index.html").read_text(encoding="utf-8").lower()
    assert_true('name="viewport"' in html, "missing viewport meta")
    assert_true("@media" in html and "max-width" in html, "missing mobile media query")
    assert_true("ai frontier radar 72h" in html or "công nghệ" in html, "missing 72h title")


def test_forbidden_public_terms_blocked() -> None:
    publication = {
        "schema_version": TECH_PUBLICATION_SCHEMA,
        "window_hours": 72,
        "executive_summary": ["Pipeline tech 24-48h có GDELT và Gemini."],
        "must_read": [],
        "sections": {
            "ai_models": [],
            "local_ai_china_ai": [],
            "ai_tools": [],
            "automation_mcp_agents": [],
            "open_source_hot": [],
            "ai_business_money": [],
            "industry_impact": [],
            "ai_knowledge": [],
            "founder_ideas_for_leon": [],
            "full_link_radar": [],
        },
        "stats": {"render_checks": {"knowledge_fields_ready": False, "founder_fields_ready": False}},
    }
    errs = validate_publication(publication, check_external=False)
    assert_true(any("contains forbidden term" in err for err in errs), "forbidden terms should fail")


def test_forbidden_diff_guard() -> None:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only"],
            cwd=ROOT,
            text=True,
        )
    except Exception:
        return
    changed = {line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()}
    bad = sorted(path for path in changed if path in FORBIDDEN_DIFF_PATHS)
    assert_true(not bad, f"forbidden paths modified: {bad}")


def main() -> None:
    test_validation_fixture_generation()
    test_api_acquisition_candidate_fixtures()
    test_publication_build_and_validate()
    test_watchlist_configured_sources_are_debug_only()
    test_manual_signal_validator_guard()
    test_frontier_watchlist_glm_5_2_fixture()
    test_multilane_frontier_fixtures_clustered()
    test_empty_must_read_guard()
    test_mobile_layout_smoke()
    test_forbidden_public_terms_blocked()
    test_forbidden_diff_guard()
    print("OK: tech pipeline tests passed")


if __name__ == "__main__":
    main()
