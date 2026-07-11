import pytest
from fastapi.testclient import TestClient

from ai_daily_update.storage.markdown import write_card
from ai_daily_update.web import create_app


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
