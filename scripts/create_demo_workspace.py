"""Create an isolated demo workspace without touching live project data."""
from pathlib import Path
import argparse
import secrets
import shutil
import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination = args.destination.resolve()
    if destination == root or root in destination.parents:
        parser.error("Choose a destination outside the repository.")
    if destination.exists():
        parser.error("Destination already exists; choose a new directory.")
    destination.mkdir(parents=True, exist_ok=False)
    config = destination / "config"
    config.mkdir()
    for name in ("app.yaml", "topics.yaml", "scoring.yaml", "prompts.yaml", "foundational_concepts.yaml"):
        shutil.copy2(root / "config" / name, config / name)
    shutil.copy2(root / "config/sources.example.yaml", config / "sources.yaml")
    app_path = config / "app.yaml"
    app = yaml.safe_load(app_path.read_text(encoding="utf-8"))
    app["daily"]["schedule"]["enabled"] = False
    app["review"]["auto"]["enabled"] = False
    app_path.write_text(yaml.safe_dump(app, allow_unicode=True, sort_keys=False), encoding="utf-8")
    for name in ("notes", "data"):
        shutil.copytree(root / "examples/demo-data" / name, destination / name)
    env = destination / ".env"
    with env.open("x", encoding="utf-8") as handle:
        env.chmod(0o600)
        handle.write("DEEPSEEK_API_KEY=\n"
                     "AI_DAILY_ADMIN_USERNAME=demo\n"
                     f"AI_DAILY_ADMIN_PASSWORD={secrets.token_urlsafe(18)}\n"
                     f"AI_DAILY_SESSION_SECRET={secrets.token_urlsafe(32)}\n")
    print(f"Created demo workspace: {destination}")
    print("Login credentials are in its .env file. Run ai-daily index from that directory.")


if __name__ == "__main__":
    main()
