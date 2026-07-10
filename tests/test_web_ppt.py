from fastapi.testclient import TestClient
import yaml
import time

from ai_daily_update.storage.markdown import write_card
from ai_daily_update.web import create_app, ppt_review_items, source_suggestion_items, split_manuscript_chunks
from ai_daily_update.config import load_settings
from ai_daily_update.ppt.decks import selected_ppt_deck


def write_ppt_test_project(root) -> None:
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "app.yaml").write_text(
        """
timezone: Asia/Shanghai
storage:
  markdown_root: notes
  sqlite_path: data/kb.sqlite
review:
  statuses:
    - needs-review
    - accepted
    - later
    - rejected
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (config_dir / "topics.yaml").write_text(
        """
topics:
  foundation-model:
    name_zh: 预训练大模型
    priority: 5
    aliases: [foundation model]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (config_dir / "sources.yaml").write_text("sources: {}\n", encoding="utf-8")
    ppt_dir = root / "ppt"
    ppt_dir.mkdir()
    (ppt_dir / "ai_frontier_ppt_structured.csv").write_text(
        "\n".join(
            [
                '"page","level1","level2","level3","content_type","content"',
                '"15","二、人工智能发展理论前沿","（一）预训练大模型","2多模态大模型","content","Gemini Robotics 推动具身智能。"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ppt_dir / "ppt_nodes.yaml").write_text(
        """
nodes:
  - node_id: theory.foundation_models.multimodal
    status: active
    role: 理论前沿
    intent: 说明多模态大模型成为具身智能基础。
    current_level1: 二、人工智能发展理论前沿
    current_level2: （一）预训练大模型
    current_level3: 2多模态大模型
    keywords: [Gemini Robotics, 具身智能]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    write_card(
        root / "notes" / "cards" / "2026" / "07" / "gemini-robotics.md",
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "Google Gemini Robotics",
            "title_en": "Google Gemini Robotics",
            "date": "2026-07-07",
            "collected_date": "2026-07-07",
            "source_url": "https://deepmind.google/models/gemini-robotics/",
            "topics": ["foundation-model"],
            "entities": ["Google DeepMind"],
            "review_status": "accepted",
        },
        "## 一句话结论\nGemini Robotics 将多模态模型扩展到具身智能。\n\n## 事件概述\nGoogle DeepMind 发布 Gemini Robotics。",
    )
    (ppt_dir / "ai_frontier_ppt_structured.md").write_text(
        "# 人工智能发展前沿 PPT 结构化文字稿\n\n## 原有讲稿\n\n- 保留内容。\n",
        encoding="utf-8",
    )


def write_source_suggestions(root) -> None:
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "ppt_source_suggestions.md").write_text(
        """
# 基于当前 PPT 结构的建议新增消息源

### P0：建议优先加入

| 建议源 | URL | 覆盖小节 | 建议 topic | 原因 |
| --- | --- | --- | --- | --- |
| Epoch AI | https://epoch.ai/ | 核心技术演进、算力趋势 | ai-compute / ai-policy | 可补训练计算和模型规模趋势。 |
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_ppt_page_lists_node_matches(tmp_path) -> None:
    write_ppt_test_project(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/ppt")

    assert response.status_code == 200
    assert "PPT 更新" in response.text
    assert "theory.foundation_models.multimodal" in response.text
    assert "已匹配" in response.text


def test_ppt_plan_action_generates_report(tmp_path) -> None:
    write_ppt_test_project(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/actions/ppt-plan",
        data={
            "preset": "custom",
            "from_date": "2026-07-07",
            "to_date": "2026-07-07",
            "date_basis": "collected",
            "status": "accepted",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/ppt?deck_id=ai-frontier-60min"
    reports = list((tmp_path / "notes" / "inbox").glob("*_ppt-update-plan*.md"))
    sidecars = list((tmp_path / "notes" / "inbox").glob("*_ppt-update-plan*.json"))
    assert len(reports) == 1
    assert len(sidecars) == 1
    report_text = reports[0].read_text(encoding="utf-8")
    sidecar_text = sidecars[0].read_text(encoding="utf-8")
    assert "Google Gemini Robotics" in report_text
    assert "第 15 页" in report_text
    assert "可修改为" in report_text
    assert "card-1" in sidecar_text
    assert "suggested_text" in sidecar_text

    page = client.get("/ppt")
    assert page.status_code == 200
    assert "当前" in page.text
    assert "改为" in page.text


def test_ppt_plan_action_can_run_as_progress_job(tmp_path) -> None:
    write_ppt_test_project(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/actions/ppt-plan",
        data={
            "preset": "custom",
            "from_date": "2026-07-07",
            "to_date": "2026-07-07",
            "date_basis": "collected",
            "status": "accepted",
        },
        headers={"X-Requested-With": "fetch"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job"]["status"] in {"queued", "running", "complete"}
    job_id = payload["job_id"]
    for _ in range(20):
        job = client.get(f"/jobs/{job_id}").json()
        if job.get("status") == "complete":
            break
        time.sleep(0.05)
    assert job["status"] == "complete"
    assert list((tmp_path / "notes" / "inbox").glob("*_ppt-update-plan*.json"))


def test_ppt_suggestion_action_marks_item_adopted(tmp_path) -> None:
    write_ppt_test_project(tmp_path)
    client = TestClient(create_app(tmp_path))
    client.post(
        "/actions/ppt-plan",
        data={
            "preset": "custom",
            "from_date": "2026-07-07",
            "to_date": "2026-07-07",
            "date_basis": "collected",
            "status": "accepted",
        },
    )
    settings = load_settings(tmp_path)
    deck = selected_ppt_deck(tmp_path)
    item = ppt_review_items(settings, deck, limit=10)[0]

    response = client.post(
        "/actions/ppt-suggestion-review",
        data={"item_id": item["id"], "status": "adopted"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    updated = {item["id"]: item for item in ppt_review_items(settings, deck, limit=10)}
    assert updated[item["id"]]["status"] == "adopted"
    links = yaml.safe_load((tmp_path / "data" / "ppt_card_links.yaml").read_text(encoding="utf-8"))
    assert links["suggestions"][item["id"]]["card_ids"]

    detail = client.get("/cards/card-1")
    assert detail.status_code == 200
    assert "PPT 使用情况" in detail.text
    assert "已写入 PPT" in detail.text


def test_source_suggestion_action_adds_source_to_config(tmp_path) -> None:
    write_ppt_test_project(tmp_path)
    write_source_suggestions(tmp_path)
    client = TestClient(create_app(tmp_path))
    settings = load_settings(tmp_path)
    suggestion = source_suggestion_items(settings)[0]

    response = client.post(
        "/actions/source-suggestion-add",
        data={"suggestion_id": suggestion["id"]},
        follow_redirects=False,
    )

    assert response.status_code == 303
    data = yaml.safe_load((tmp_path / "config" / "sources.yaml").read_text(encoding="utf-8"))
    sources = data["sources"]["company_blogs"]["sources"]
    assert any(source["name"] == "Epoch AI" for source in sources)
    options = data["sources"]["source_topics"]
    assert {"id": "ai-compute", "label": "AI 算力"} in options


def test_source_suggestion_action_returns_json_for_fetch_requests(tmp_path) -> None:
    write_ppt_test_project(tmp_path)
    write_source_suggestions(tmp_path)
    client = TestClient(create_app(tmp_path))
    settings = load_settings(tmp_path)
    suggestion = source_suggestion_items(settings)[0]

    response = client.post(
        "/actions/source-suggestion-add",
        data={"suggestion_id": suggestion["id"], "return_to": "/sources"},
        headers={"X-Requested-With": "fetch", "Accept": "application/json"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["suggestion_id"] == suggestion["id"]
    assert payload["status"] == "added"
    assert payload["status_label"] == "已加入"
    assert 'data-source-suggestion-actions' in payload["actions_html"]


def test_ppt_manuscript_import_and_save(tmp_path) -> None:
    write_ppt_test_project(tmp_path)
    client = TestClient(create_app(tmp_path))
    client.post(
        "/actions/ppt-plan",
        data={
            "preset": "custom",
            "from_date": "2026-07-07",
            "to_date": "2026-07-07",
            "date_basis": "collected",
            "status": "accepted",
        },
    )
    settings = load_settings(tmp_path)
    deck = selected_ppt_deck(tmp_path)
    item = ppt_review_items(settings, deck, limit=10)[0]
    client.post(
        "/actions/ppt-suggestion-review",
        data={"item_id": item["id"], "status": "accepted"},
    )

    response = client.post("/actions/ppt-manuscript-import", follow_redirects=False)

    assert response.status_code == 303
    manuscript = (tmp_path / "ppt" / "ai_frontier_ppt_structured.md").read_text(encoding="utf-8")
    assert "自动导入的 PPT 更新建议" in manuscript
    assert "Google Gemini Robotics" in manuscript
    assert list((tmp_path / "ppt" / "backups").glob("*.md"))

    response = client.post(
        "/actions/ppt-manuscript-save",
        data={"content": "# 修改后的讲稿\n"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert (tmp_path / "ppt" / "ai_frontier_ppt_structured.md").read_text(encoding="utf-8") == "# 修改后的讲稿\n"


def test_ppt_manuscript_section_editor_saves_chunks(tmp_path) -> None:
    write_ppt_test_project(tmp_path)
    (tmp_path / "ppt" / "ai_frontier_ppt_structured.md").write_text(
        "# 一级：理论前沿\n\n## 二级：预训练大模型\n\n### 1 三级：多模态大模型\n<!-- slide: 1 -->\n- 原始内容。\n",
        encoding="utf-8",
    )
    client = TestClient(create_app(tmp_path))

    page = client.get("/ppt")
    assert page.status_code == 200
    assert "按标题层级编辑讲稿" in page.text
    assert "一级：理论前沿" in page.text
    assert "二级：预训练大模型" in page.text
    assert "1 三级：多模态大模型" in page.text

    response = client.post(
        "/actions/ppt-manuscript-sections-save",
        data={
            "chunk_content": [
                "# 人工智能发展前沿 PPT 结构化文字稿\n\n## 原有讲稿",
                "### 1 测试小节\n<!-- slide: 1 -->\n- 更新后的分段内容。",
            ]
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    manuscript = (tmp_path / "ppt" / "ai_frontier_ppt_structured.md").read_text(encoding="utf-8")
    assert "### 1 测试小节" in manuscript
    assert "更新后的分段内容" in manuscript


def test_split_manuscript_chunks_keeps_level2_only_sections() -> None:
    chunks = split_manuscript_chunks(
        "# 一、人工智能发展简介\n\n"
        "## （一）人工智能概念\n"
        "### 1 什么是智能？\n"
        "- 智能就是学习的能力。\n\n"
        "## （二）人工智能发展历程\n"
        "<!-- slide: 6 -->\n"
        "- 1997年：Deep Blue 战胜国际象棋冠军。\n"
    )

    sections = [chunk for chunk in chunks if chunk["kind"] == "section"]

    assert [section["title"] for section in sections] == ["1 什么是智能？", ""]
    assert sections[1]["level1"] == "一、人工智能发展简介"
    assert sections[1]["level2"] == "（二）人工智能发展历程"
    assert sections[1]["level3"] == ""
    assert sections[1]["page"] == "6"


def test_ppt_template_download_and_deck_upload(tmp_path) -> None:
    write_ppt_test_project(tmp_path)
    client = TestClient(create_app(tmp_path))

    template_response = client.get("/ppt/template")

    assert template_response.status_code == 200
    assert "PPT 结构化文字稿" in template_response.text

    manuscript = """
# 新报告 PPT 结构化文字稿

# 一、第一部分

## （一）小节

### 1 主题

<!-- slide: 1 -->
- 这是新报告内容。
""".strip()
    response = client.post(
        "/actions/ppt-deck-upload",
        data={
            "deck_id": "new-report-30min",
            "title": "新报告",
            "version": "30分钟版",
            "duration": "30",
            "manuscript_text": manuscript,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/ppt?deck_id=new-report-30min"
    deck_dir = tmp_path / "ppt" / "decks" / "new-report-30min"
    assert (deck_dir / "manuscript.md").exists()
    assert (deck_dir / "structured.csv").exists()
    assert (deck_dir / "nodes.yaml").exists()
    decks_yaml = yaml.safe_load((tmp_path / "ppt" / "decks.yaml").read_text(encoding="utf-8"))
    assert any(item["id"] == "new-report-30min" for item in decks_yaml["decks"])
