import importlib.util
import json
from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from ai_daily_update.learning import choose_news_concepts_with_llm, plan_for_targets, search_items
from ai_daily_update.storage.markdown import write_card
from ai_daily_update.web import create_app, learning_card_recommendations, map_custom_goal_with_llm, safe_source_url


def item(name, required=(), status="reviewed"):
    return {
        "id": f"concept:{name}", "type": "concept", "title": name, "aliases": [name],
        "source_section": "2.2.2", "review_status": status,
        "reviewed_by": "teacher", "reviewed_at": "2026-10-02",
        "explanation": f"{name}的解释", "example": "一个具体例子", "misconception": "常见误解",
        "question": "检查题", "answer": "参考答案",
        "prerequisites": {"required": list(required), "helpful": [], "advanced": []},
    }


def test_search_and_required_path_skip_unreviewed_and_optional_links(tmp_path):
    folder = tmp_path / "content" / "learning"
    folder.mkdir(parents=True)
    folder.joinpath("catalog.json").write_text(json.dumps({"complete": True, "items": [
        item("张量"), item("梯度下降", ["concept:张量"]), item("伦理", status="draft"),
    ]}, ensure_ascii=False), encoding="utf-8")
    from ai_daily_update.learning import load_catalog
    catalog = load_catalog(tmp_path)
    assert [result["title"] for result in search_items(catalog, "梯度下降")] == ["梯度下降"]
    assert search_items(catalog, "伦理") == []
    assert [step["id"] for step in plan_for_targets(catalog, ["concept:梯度下降"])] == ["concept:张量", "concept:梯度下降"]
    assert [step["id"] for step in plan_for_targets(catalog, ["concept:梯度下降"], ["concept:张量"])] == ["concept:梯度下降"]
    catalog["items"][0]["prerequisites"]["required"] = ["concept:梯度下降"]
    with pytest.raises(ValueError, match="cycle"):
        plan_for_targets(catalog, ["concept:梯度下降"])


def test_search_finds_a_concept_from_its_check_question():
    concept = item("梯度下降")
    concept["question"] = "为什么训练时需要控制参数更新幅度？"
    catalog = {"items": [concept, item("张量")]}
    assert [result["title"] for result in search_items(catalog, "参数更新幅度太大怎么办？")] == ["梯度下降"]


def setup_site(tmp_path, enabled=True):
    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text(f"auth:\n  enabled: false\ndaily:\n  schedule:\n    enabled: false\nstorage:\n  markdown_root: notes\n  sqlite_path: data/kb.sqlite\nlearning:\n  enabled: {str(enabled).lower()}\n  expected_count: 2\nllm:\n  model: test-model\n", encoding="utf-8")
    for name in ("topics", "sources", "foundational_concepts", "scoring", "prompts"):
        (config / f"{name}.yaml").write_text("{}\n", encoding="utf-8")
    folder = tmp_path / "content" / "learning"
    folder.mkdir(parents=True)
    folder.joinpath("catalog.json").write_text(json.dumps({"complete": True, "items": [item("张量"), item("梯度下降", ["concept:张量"])]}, ensure_ascii=False), encoding="utf-8")
    return TestClient(create_app(tmp_path))


def test_public_learning_routes_and_goal(tmp_path):
    client = setup_site(tmp_path)
    path_page = client.get("/learn")
    chat_page = client.get("/learn/chat")
    assert path_page.status_code == chat_page.status_code == 200
    assert "learning-plan-form" in path_page.text and "learning-chat-form" not in path_page.text
    assert "learning-chat-form" in chat_page.text and "learning-plan-form" not in chat_page.text
    assert 'href="/learn/chat"' in path_page.text
    assert 'href="/learn"' in chat_page.text
    assert client.get("/api/v1/learning/concepts?q=张量").json()["items"][0]["title"] == "张量"
    assert client.get("/learn/concepts/concept:张量").status_code == 200
    plan = client.post("/api/v1/learning/plan", json={"goal_text": "梯度下降", "background": "beginner"}).json()
    assert [step["id"] for step in plan["steps"]] == ["concept:张量", "concept:梯度下降"]
    assert client.post("/api/v1/learning/plan", json={"goal_text": "无法匹配的领域"}).json()["steps"] == []


def test_learning_is_closed_until_enabled(tmp_path):
    client = setup_site(tmp_path, enabled=False)
    assert client.get("/learn").status_code == 404
    assert client.get("/learn/chat").status_code == 404
    assert client.post("/api/v1/learning/chat", json={"message": "张量是什么"}).status_code == 404
    assert client.post("/api/v1/learning/render", json={"messages": ["**张量**"]}).status_code == 404


def test_learning_plan_is_public_with_admin_login_enabled(tmp_path):
    setup_site(tmp_path)
    (tmp_path / "config" / "app.yaml").write_text("auth:\n  enabled: true\n  username: admin\n  password: test-secret\n  session_secret: test-session-secret\ndaily:\n  schedule:\n    enabled: false\nlearning:\n  enabled: true\n  expected_count: 2\n", encoding="utf-8")
    client = TestClient(create_app(tmp_path))
    response = client.post("/api/v1/learning/plan", json={"goal_text": "梯度下降"})
    assert response.status_code == 200
    assert response.json()["steps"]
    rendered = client.post("/api/v1/learning/render", json={"messages": ["**重点**"]})
    assert rendered.status_code == 200
    assert "<strong>重点</strong>" in rendered.json()["html"][0]


def test_chat_uses_only_accepted_news(tmp_path, monkeypatch):
    client = setup_site(tmp_path)
    for card_id, status in (("accepted", "accepted"), ("auto", "accepted"), ("draft", "needs-review")):
        write_card(tmp_path / "notes" / "cards" / f"{card_id}.md", {
            "id": card_id, "title_zh": "发布张量模型", "date": "2026-10-02", "event_date": "2026-10-02",
            "track": "industry", "review_status": status, "topics": [], "entities": [],
            "reviewed_by": "auto" if card_id == "auto" else "teacher" if card_id == "accepted" else "",
            "reviewed_at": "2026-10-02" if card_id != "draft" else "",
            "learning_concept_ids": ["concept:张量"],
        }, "## 一句话结论\n发布了一个张量模型。")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    captured = {}

    def fake_reply(self, instructions, prompt):
        captured["prompt"] = prompt
        return "解释和例子。[1]"

    monkeypatch.setattr("ai_daily_update.web.OpenAIClient.generate_learning_reply", fake_reply)
    accepted = client.post("/api/v1/learning/chat", json={"message": "这条消息里的张量是什么？", "card_id": "accepted"})
    assert accepted.status_code == 200
    assert "参考答案：参考答案" in captured["prompt"]
    assert any(source["type"] == "news" and source["id"] == "accepted" for source in accepted.json()["sources"])
    monkeypatch.setattr("ai_daily_update.web.OpenAIClient.generate_learning_reply", lambda self, instructions, prompt: "解释和例子。[citation:1]")
    assert client.post("/api/v1/learning/chat", json={"message": "张量是什么"}).json()["answer"] == "解释和例子。[1]"
    monkeypatch.setattr("ai_daily_update.web.OpenAIClient.generate_learning_reply", lambda self, instructions, prompt: "无效来源。[citation:999]")
    assert client.post("/api/v1/learning/chat", json={"message": "张量是什么"}).json()["error"] == "model_unverified"
    monkeypatch.setattr("ai_daily_update.web.OpenAIClient.generate_learning_reply", lambda self, instructions, prompt: "没有引用的回答")
    assert client.post("/api/v1/learning/chat", json={"message": "张量是什么"}).json()["error"] == "model_unverified"
    assert client.post("/api/v1/learning/chat", json={"message": "请解释", "card_id": "draft"}).status_code == 404
    assert client.post("/api/v1/learning/chat", json={"message": "请解释", "card_id": "auto"}).status_code == 404
    auto_detail = client.get("/public/cards/auto").text
    assert "对应的教材知识点" in auto_detail
    assert '/learn/concepts/concept:张量' in auto_detail
    assert "与学习助手讨论这条消息" not in auto_detail
    assert '/learn/concepts/concept:张量' in client.get("/cards/auto").text
    unrelated = client.post("/api/v1/learning/chat", json={"message": "天气如何"})
    assert unrelated.status_code == 200
    assert unrelated.json()["sources"] == []


def test_chat_resolves_english_term_to_reviewed_concept(tmp_path, monkeypatch):
    setup_site(tmp_path)
    path = tmp_path / "content" / "learning" / "catalog.json"
    path.write_text(json.dumps({"complete": True, "items": [item("智能体定义与类型"), item("智能体系统")]}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    replies = iter(["智能体能感知环境并采取行动。", "智能体能感知环境并采取行动。[1]"])

    def fake_reply(self, instructions, prompt):
        if "仅从列表中选出" in instructions:
            return '["智能体定义与类型"]'
        assert "智能体定义与类型" in prompt
        return next(replies)

    monkeypatch.setattr("ai_daily_update.web.OpenAIClient.generate_learning_reply", fake_reply)
    response = TestClient(create_app(tmp_path)).post("/api/v1/learning/chat", json={"message": "agent是什么"})
    assert response.status_code == 200
    assert response.json()["sources"][0]["title"] == "智能体定义与类型"
    assert "智能体能感知环境" in response.json()["answer"]


def test_learning_rejects_oversized_known_id(tmp_path):
    client = setup_site(tmp_path)
    response = client.post("/api/v1/learning/plan", json={"goal_text": "张量", "known_ids": ["x" * 121]})
    assert response.status_code == 422


def test_incomplete_catalog_does_not_publish_extra_reviewed_items(tmp_path):
    setup_site(tmp_path)
    path = tmp_path / "content" / "learning" / "catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    catalog["items"].append(item("草稿", status="draft"))
    path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    client = TestClient(create_app(tmp_path))
    assert client.get("/learn").status_code == 404


def test_invalid_model_goal_mapping_does_not_crash(tmp_path, monkeypatch):
    setup_site(tmp_path)
    from ai_daily_update.config import load_settings
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("ai_daily_update.web.OpenAIClient.generate_learning_reply", lambda self, instructions, prompt: '[{"id": "concept:张量"}]')
    assert map_custom_goal_with_llm(load_settings(tmp_path), {"items": [item("张量")]}, "学张量") == []


def test_custom_agent_goal_accepts_reviewed_concept_titles(tmp_path, monkeypatch):
    setup_site(tmp_path)
    path = tmp_path / "content" / "learning" / "catalog.json"
    path.write_text(json.dumps({"complete": True, "items": [item("智能体系统"), item("任务规划与工具调用")]}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("ai_daily_update.web.OpenAIClient.generate_learning_reply", lambda self, instructions, prompt: '["智能体系统", "任务规划与工具调用"]')
    response = TestClient(create_app(tmp_path)).post("/api/v1/learning/plan", json={"goal_text": "想要自己搭一个agent"})
    assert [step["title"] for step in response.json()["steps"]] == ["智能体系统", "任务规划与工具调用"]


def test_learning_markdown_renders_formatting_without_raw_html(tmp_path):
    client = setup_site(tmp_path)
    response = client.post("/api/v1/learning/render", json={"messages": ["## 步骤\n\n- **第一步**：运行 `python`", "<script>alert(1)</script>\n\n[bad](javascript:alert(1))\n\n![remote](https://example.com/a.png)"]})
    assert response.status_code == 200
    html = response.json()["html"]
    assert "<h2>步骤</h2>" in html[0] and "<strong>第一步</strong>" in html[0]
    assert "<script>" not in html[1] and 'href="javascript:' not in html[1]
    assert "<img" not in html[1]


def test_public_source_link_requires_http_scheme():
    assert safe_source_url("javascript:alert(1)") == ""
    assert safe_source_url("data:text/html,<script>alert(1)</script>") == ""
    assert safe_source_url("https://example.com/news") == "https://example.com/news"
    assert safe_source_url("https://[broken") == ""


def test_generation_matches_only_reviewed_catalog_ids_and_page_uses_saved_match():
    catalog = {"complete": True, "items": [item("张量"), item("梯度下降")]}

    class FakeLLM:
        available = True

        def generate_card_content(self, prompt):
            assert "concept:张量" in prompt
            return '["concept:张量", "concept:编造", "concept:张量"]'

    ids = choose_news_concepts_with_llm(catalog, {"title_zh": "张量新闻"}, "正文", FakeLLM())
    assert ids == ["concept:张量"]
    recommendations = learning_card_recommendations(catalog, {"learning_concept_ids": ids})
    assert [result["id"] for result in recommendations] == ids
    assert learning_card_recommendations(catalog, {"learning_concept_ids": []}) == []
    assert learning_card_recommendations(catalog, {"title_zh": "张量"}) == []


def test_generation_can_match_reviewed_microtopics_without_treating_invalid_ids_as_no_fit():
    microtopic = {**item("向量检索"), "id": "microtopic:向量检索", "type": "microtopic"}
    catalog = {"complete": True, "items": [item("机器学习"), microtopic]}

    class FakeLLM:
        available = True
        response = '["向量检索", "concept:编造", "microtopic:向量检索"]'

        def generate_card_content(self, prompt):
            assert "microtopic:向量检索" in prompt
            assert "向量检索的解释" in prompt
            return self.response

    llm = FakeLLM()
    ids = choose_news_concepts_with_llm(catalog, {"title_zh": "向量检索新闻"}, "正文", llm)
    assert ids == ["microtopic:向量检索"]
    recommendations = learning_card_recommendations(catalog, {"learning_concept_ids": ids})
    assert [item["id"] for item in recommendations] == ids
    assert recommendations[0]["title"] == "机器学习 · 向量检索"
    llm.response = '["concept:编造"]'
    assert choose_news_concepts_with_llm(catalog, {}, "", llm) is None
    catalog["items"].append({**microtopic, "id": "microtopic:另一个向量检索"})
    llm.response = '["向量检索"]'
    assert choose_news_concepts_with_llm(catalog, {}, "", llm) is None
    llm.response = "[]"
    assert choose_news_concepts_with_llm(catalog, {}, "", llm) == []


def test_export_rejects_draft_and_missing_review_fields(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts" / "export_learning_content.py"
    spec = importlib.util.spec_from_file_location("learning_export", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "WIKI", tmp_path)
    monkeypatch.setattr(module, "EXPECTED", {"concepts": 1, "microtopics": 0, "synthesis": 0})
    folder = tmp_path / "concepts"
    folder.mkdir()
    (folder / "张量.md").write_text("---\ntype: concept\ntitle: 张量\nsource_section: '2.2.1'\nreview_status: draft\n---\n# 张量\n", encoding="utf-8")
    items, issues = module.collect()
    assert items == []
    assert any("review_status=reviewed" in issue for issue in issues)
    (folder / "张量.md").write_text("""---
type: concept
title: 张量
source_section: '2.2.1'
review_status: reviewed
reviewed_by: 教师甲
reviewed_at: '2026-10-02'
formula_checked: true
figures_checked: true
aliases: [张量]
explanation: 多维数据表示
example: 一张彩色图片
misconception: 不等于神经网络
question: 图片有几个维度？
answer: 高宽通道三个维度。
prerequisites: {required: [], helpful: [], advanced: []}
---
# 张量
""", encoding="utf-8")
    items, issues = module.collect()
    assert not issues
    assert items[0]["id"] == "concept:张量"
    assert "raw/sources" not in json.dumps(items, ensure_ascii=False)


def test_export_ignores_explicit_supplemental_draft(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts" / "export_learning_content.py"
    spec = importlib.util.spec_from_file_location("learning_export", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "WIKI", tmp_path)
    monkeypatch.setattr(module, "EXPECTED", {"concepts": 0})
    folder = tmp_path / "concepts"
    folder.mkdir()
    (folder / "补充草稿.md").write_text("---\nlearning_catalog: false\nreview_status: draft\n---\n", encoding="utf-8")
    items, issues = module.collect()
    assert items == []
    assert issues == []
