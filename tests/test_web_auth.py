import pytest
from fastapi.testclient import TestClient

from ai_daily_update.storage.markdown import read_card, write_card
from ai_daily_update.web import create_app
from ai_daily_update.web import safe_return_to
from ai_daily_update.cli import _llm_client
from ai_daily_update.config import load_settings


def write_auth_config(root) -> None:
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "app.yaml").write_text(
        """
timezone: Asia/Shanghai
auth:
  enabled: true
  username: reviewer
  password: secret
  session_secret: test-secret
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
    (config_dir / "sources.yaml").write_text("sources: {}\n", encoding="utf-8")
    (config_dir / "topics.yaml").write_text("topics: {}\n", encoding="utf-8")


def test_auth_redirects_anonymous_users_to_login(tmp_path) -> None:
    write_auth_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/cards", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_auth_rejects_bad_password(tmp_path) -> None:
    write_auth_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/login",
        data={"username": "reviewer", "password": "wrong"},
    )

    assert response.status_code == 401
    assert "用户名或密码不正确" in response.text


def test_auth_login_allows_access(tmp_path) -> None:
    write_auth_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    login = client.post(
        "/login",
        data={"username": "reviewer", "password": "secret"},
        follow_redirects=False,
    )
    response = client.get("/")

    assert login.status_code == 303
    assert "ai_daily_session" in login.headers["set-cookie"]
    assert response.status_code == 200
    assert "每日工作台" in response.text


def test_admin_can_update_model_and_key_without_exposing_key(tmp_path, monkeypatch) -> None:
    write_auth_config(tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("AI_DAILY_LLM_MODEL", raising=False)
    client = TestClient(create_app(tmp_path))
    assert client.get("/model-settings", follow_redirects=False).status_code == 303
    assert client.post("/actions/model-settings", data={"model": "deepseek-flash", "api_key": "fake-key"}, follow_redirects=False).status_code == 303
    assert not (tmp_path / ".env").exists()

    client.post("/login", data={"username": "reviewer", "password": "secret"})
    assert client.post("/actions/model-settings", data={"model": "invalid model", "api_key": "fake-key"}).status_code == 400
    assert not (tmp_path / ".env").exists()
    response = client.post("/actions/model-settings", data={"model": "deepseek-flash", "api_key": "fake-key"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/model-settings?saved=1"
    assert "DEEPSEEK_API_KEY" in (tmp_path / ".env").read_text(encoding="utf-8")
    page = client.get("/model-settings")
    assert page.status_code == 200
    assert "deepseek-flash" in page.text and "已配置" in page.text
    assert "fake-key" not in page.text
    assert _llm_client(load_settings(tmp_path)).model == "deepseek-flash"

    client.post("/actions/model-settings", data={"model": "deepseek-reasoner", "api_key": ""})
    assert _llm_client(load_settings(tmp_path)).model == "deepseek-reasoner"
    assert (tmp_path / ".env").read_text(encoding="utf-8").count("fake-key") == 1


def test_extra_admin_login_preserves_primary_account(tmp_path, monkeypatch) -> None:
    write_auth_config(tmp_path)
    monkeypatch.setenv("AI_DAILY_EXTRA_ADMIN_USERNAME", "gan")
    monkeypatch.setenv("AI_DAILY_EXTRA_ADMIN_PASSWORD", "extra-secret")
    client = TestClient(create_app(tmp_path))

    for username, password in (("reviewer", "secret"), ("gan", "extra-secret")):
        login = client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )
        assert login.status_code == 303
        assert client.get("/cards").status_code == 200
        client.cookies.clear()


def test_duplicate_admin_names_are_rejected(tmp_path, monkeypatch) -> None:
    write_auth_config(tmp_path)
    monkeypatch.setenv("AI_DAILY_EXTRA_ADMIN_USERNAME", "reviewer")
    monkeypatch.setenv("AI_DAILY_EXTRA_ADMIN_PASSWORD", "other-secret")
    with pytest.raises(RuntimeError, match="distinct"):
        create_app(tmp_path)


def test_example_credentials_are_rejected(tmp_path) -> None:
    write_auth_config(tmp_path)
    path = tmp_path / "config" / "app.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("  password: secret", "  password: change_me"), encoding="utf-8")
    with pytest.raises(RuntimeError, match="example admin password"):
        create_app(tmp_path)


def test_return_address_cannot_leave_site() -> None:
    assert safe_return_to("/cards?page=2", "/") == "/cards?page=2"
    for value in ("https://evil.example", "//evil.example", "/\\evil.example", "/cards\nLocation: https://evil.example"):
        assert safe_return_to(value, "/") == "/"


def test_manual_acceptance_records_human_reviewer(tmp_path) -> None:
    write_auth_config(tmp_path)
    path = tmp_path / "notes" / "cards" / "news.md"
    write_card(path, {"id": "news", "title_zh": "新闻", "review_status": "needs-review"}, "内容")
    client = TestClient(create_app(tmp_path))
    client.post("/login", data={"username": "reviewer", "password": "secret"})
    response = client.post("/actions/review", data={"card_id": "news", "status": "accepted", "return_to": "//evil.example"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/cards"
    metadata = read_card(path).metadata
    assert metadata["reviewed_by"] == "reviewer"
    assert metadata["reviewed_at"]


def test_admin_action_rejects_foreign_origin(tmp_path) -> None:
    write_auth_config(tmp_path)
    client = TestClient(create_app(tmp_path))
    client.post("/login", data={"username": "reviewer", "password": "secret"})
    response = client.post("/actions/index", headers={"Origin": "https://evil.example"}, follow_redirects=False)
    assert response.status_code == 403


def test_changing_password_invalidates_existing_session(tmp_path) -> None:
    write_auth_config(tmp_path)
    client = TestClient(create_app(tmp_path))
    client.post("/login", data={"username": "reviewer", "password": "secret"})
    assert client.get("/cards").status_code == 200
    path = tmp_path / "config" / "app.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("  password: secret", "  password: new-secret"), encoding="utf-8")
    other = TestClient(create_app(tmp_path))
    other.cookies.update(client.cookies)
    assert other.get("/cards", follow_redirects=False).status_code == 303


def test_auth_settings_rejects_enabled_without_credentials(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("AI_DAILY_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("AI_DAILY_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("AI_DAILY_SESSION_SECRET", raising=False)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "app.yaml").write_text("auth:\n  enabled: true\n", encoding="utf-8")
    (config_dir / "sources.yaml").write_text("sources: {}\n", encoding="utf-8")
    (config_dir / "topics.yaml").write_text("topics: {}\n", encoding="utf-8")

    with pytest.raises(RuntimeError):
        create_app(tmp_path)


def test_login_locks_out_after_repeated_failures(tmp_path) -> None:
    write_auth_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    for _ in range(5):
        client.post("/login", data={"username": "reviewer", "password": "wrong"})
    response = client.post("/login", data={"username": "reviewer", "password": "secret"})

    assert response.status_code == 429


def test_logout_invalidates_existing_session_cookie(tmp_path) -> None:
    write_auth_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    client.post("/login", data={"username": "reviewer", "password": "secret"})
    session_cookie = client.cookies.get("ai_daily_session")

    client.post("/logout")
    client.cookies.set("ai_daily_session", session_cookie)
    response = client.get("/cards", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_sets_secure_cookie_over_https(tmp_path) -> None:
    write_auth_config(tmp_path)
    client = TestClient(create_app(tmp_path), base_url="https://testserver")

    response = client.post(
        "/login",
        data={"username": "reviewer", "password": "secret"},
        follow_redirects=False,
    )

    assert "secure" in response.headers["set-cookie"].lower()


def test_login_can_require_secure_cookie_behind_proxy(tmp_path) -> None:
    write_auth_config(tmp_path)
    path = tmp_path / "config" / "app.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("  enabled: true", "  enabled: true\n  cookie_secure: true", 1), encoding="utf-8")
    client = TestClient(create_app(tmp_path))
    response = client.post("/login", data={"username": "reviewer", "password": "secret"}, follow_redirects=False)
    assert "secure" in response.headers["set-cookie"].lower()


def test_anonymous_root_shows_public_cards(tmp_path) -> None:
    write_auth_config(tmp_path)
    write_card(
        tmp_path / "notes" / "cards" / "2026" / "07" / "public.md",
        {
            "id": "public-1",
            "track": "industry",
            "title_zh": "公开卡片",
            "date": "2026-07-08",
            "event_date": "2026-06-04",
            "source_url": "https://example.com",
            "topics": [],
            "entities": [],
            "review_status": "needs-review",
        },
        "## 一句话结论\n公开展示。",
    )
    client = TestClient(create_app(tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "知识卡片" in response.text
    assert "公开卡片" in response.text
    assert "管理工作台" not in response.text
