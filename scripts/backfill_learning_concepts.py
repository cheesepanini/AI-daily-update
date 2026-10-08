"""Attach AI-selected textbook concepts to existing news cards."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys

from ai_daily_update.cli import _llm_client
from ai_daily_update.config import load_settings
from ai_daily_update.learning import choose_news_concepts_with_llm, load_catalog
from ai_daily_update.storage.markdown import iter_cards, read_card, update_metadata


def main() -> None:
    settings = load_settings(Path.cwd())
    catalog = load_catalog(settings.root)
    llm = _llm_client(settings)
    if not catalog.get("complete") or not llm.available:
        raise SystemExit("Reviewed catalog or model API is unavailable")
    cards = [read_card(path) for path in iter_cards(settings.markdown_root)]
    retry_empty = "--retry-empty" in sys.argv[1:]
    cards = [card for card in cards if "learning_concept_ids" not in card.metadata or (retry_empty and card.metadata["learning_concept_ids"] == [])]
    matched = empty = failed = 0
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(choose_news_concepts_with_llm, catalog, card.metadata, card.content, llm): card for card in cards}
        for future in as_completed(futures):
            card = futures[future]
            try:
                ids = future.result()
            except Exception:
                ids = None
            if ids is None:
                failed += 1
                print(f"failed {card.metadata.get('id', card.path.stem)}", flush=True)
                continue
            update_metadata(card.path, {"learning_concept_ids": ids})
            matched += bool(ids)
            empty += not ids
            print(f"processed={matched + empty + failed}/{len(cards)} matched={matched} empty={empty} failed={failed}", flush=True)
    print(f"done total={len(cards)} matched={matched} empty={empty} failed={failed}", flush=True)


if __name__ == "__main__":
    main()
