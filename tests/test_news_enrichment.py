import json
from io import BytesIO
from types import SimpleNamespace

from PIL import Image
from fastapi.testclient import TestClient

from ai_daily_update import news_enrichment as enrichment, news_media
from ai_daily_update.cli import _prompt_for_candidate
from ai_daily_update.collectors.document import SourceDocument
from ai_daily_update.collectors.web_page import extract_document_from_html
from ai_daily_update.processors.card_builder import apply_source_evidence
from ai_daily_update.processors.candidates import Candidate
from ai_daily_update.storage.markdown import read_card, write_card
from ai_daily_update.web import create_app


def test_same_event_requires_actual_body_quote_and_specific_shared_identity():
    original = SourceDocument('https://primary.example/news', 'Launch of Orion 3', '',
                              'Orion 3 is released with a new coding mode.')
    other = SourceDocument('https://other.example/report', 'Orion 3 release', '',
                           'The new Orion 3 release includes a coding mode for developers.')
    choices = [{'index': 0, 'anchor': 'Orion 3', 'quote': other.text}]
    llm = SimpleNamespace(available=True, generate_learning_reply=lambda *_: json.dumps(choices))
    assert enrichment.verify_event_sources(llm, original, original.title, [other])[0][1]['url'] == other.url
    choices[0]['quote'] = 'A fabricated Orion 3 quote that is not in the article.'
    assert enrichment.verify_event_sources(llm, original, original.title, [other]) == []
    choices[0] = {'index': 0, 'anchor': 'OpenAI', 'quote': other.text}
    assert enrichment.verify_event_sources(llm, original, original.title, [other]) == []
    choices[0] = {'index': True, 'anchor': 'Orion 3', 'quote': other.text}
    assert enrichment.verify_event_sources(llm, original, original.title, [other]) == []
    original = SourceDocument(original.url, 'Release of Qwen4-Max', '', 'Qwen4-Max improves coding.')
    other = SourceDocument(other.url, 'Qwen4-Max', '', 'Qwen4-Max completes coding tasks at a lower cost.')
    choices[0] = {'index': 0, 'anchor': 'Qwen4-Max is cheaper for coding tasks', 'quote': other.text}
    assert enrichment.verify_event_sources(llm, original, original.title, [other])[0][1]['anchor'] == 'Qwen4-Max'
    other = SourceDocument(other.url, other.title, '', 'Qwen4-Max\n完成任务的平均费用\n降低了\n58%。' * 15)
    choices[0] = {'index': 0, 'anchor': 'Qwen4-Max', 'quote': other.text.replace('\n', '')}
    assert len(enrichment.verify_event_sources(llm, original, original.title, [other])[0][1]['quote']) == 220
    choices[0]['quote'] += '这一句并不存在于原文。'
    assert enrichment.verify_event_sources(llm, original, original.title, [other]) == []


def test_cross_source_material_enters_generation_and_preserves_image_origin(monkeypatch, tmp_path):
    first = 'https://primary.example/story'
    second = 'https://reporter.example/orion-3'
    image_url = 'https://reporter.example/orion-3-demo.png'
    original = SourceDocument(first, 'Orion 3 release', '', 'Orion 3 is released.')
    other = SourceDocument(second, 'Orion 3 coding demo', '', 'Orion 3 is released with a new coding mode.',
                           images=({'url': image_url, 'caption': 'Orion 3 coding demonstration'},))
    replies = iter([['Orion 3 release'], [{'index': 0, 'url': 'https://invented.example/not-fetched'}],
                    [{'index': 0, 'anchor': 'Orion 3', 'quote': other.text}]])
    llm = SimpleNamespace(available=True, generate_learning_reply=lambda *_: json.dumps(next(replies)))
    monkeypatch.setattr(enrichment, 'search_event_pages', lambda _: [{'url': second, 'title': other.title}])
    monkeypatch.setattr(enrichment, '_fetch_related', lambda _: other)
    result = enrichment.enrich_news_sources(llm, original, original.title)
    assert result.url == first and result.text == original.text
    assert result.images[0]['source_page'] == second
    candidate = Candidate(first, 'industry', [], original.title)
    metadata = {'id': 'orion', 'source_url': first, 'news_dates': {}}
    apply_source_evidence(metadata, candidate, result)
    assert 'excerpt' not in metadata['supplementary_sources'][0]
    prompt = _prompt_for_candidate(candidate, result)
    assert second in prompt and other.text in prompt
    buffer = BytesIO()
    Image.new('RGB', (800, 500), 'blue').save(buffer, format='PNG')
    requested = []

    def prepare(root, url, *, source_page):
        requested.append((url, source_page))
        return news_media.store_news_image(root, buffer.getvalue())

    monkeypatch.setattr(news_media, 'prepare_image', prepare)
    assert news_media.publish_verified_images(tmp_path, metadata, result) == 1
    approved = news_media.approved_images(metadata, 'orion')
    assert requested == [(image_url, second)]
    assert approved[0]['page'] == first and approved[0]['source_page'] == second
    metadata.update(title_zh='Orion 3 发布', review_status='accepted', date='2026-11-10', track='industry')
    (tmp_path / 'config').mkdir()
    (tmp_path / 'config/app.yaml').write_text('auth: {enabled: false}\n', encoding='utf-8')
    write_card(tmp_path / 'notes/cards/orion.md', metadata, '## 一句话结论\nOrion 3 发布。')
    client = TestClient(create_app(tmp_path))
    html = client.get('/public/cards/orion').text
    assert f'href="{second}"' in html and '补充报道与资料' in html
    metadata['source_url'] = 'https://primary.example/different-story'
    assert news_media.approved_images(metadata, 'orion') == []
    write_card(tmp_path / 'notes/cards/orion.md', metadata, '## 一句话结论\nOrion 3 发布。')
    assert '补充报道与资料' not in client.get('/public/cards/orion').text


def test_digest_does_not_publish_its_parent_cover_or_another_items_picture(monkeypatch):
    document = SourceDocument('https://media.example/digest', 'AI速递', '',
        '一、Orion 3 发布\n全新版本已经发布，包含新的编程能力和测试结果。\n二、其他事件\n另一个事件的消息内容足够长，包含新的研究进展。',
        images=({'url': 'https://media.example/unrelated-cover.jpg', 'caption': '合集封面'},))
    result = enrichment.enrich_news_sources(SimpleNamespace(available=False), document, 'Orion 3 发布', digest_index=1)
    assert not result.images


def test_html_discovery_keeps_article_links_and_exact_paper_version_is_checked(monkeypatch):
    doc = extract_document_from_html('https://publisher.example/news', '''
        <title>Orion 3</title><nav><a href="https://advert.example/offer">ad</a></nav>
        <article><a href="https://project.example/orion-3">Project</a>
        <a href="https://publisher.example/contact">Contact</a></article>
    ''')
    assert doc.links == ({'url': 'https://project.example/orion-3', 'title': 'Project'},)
    paper = SourceDocument('https://arxiv.org/abs/2611.12345v1', 'A distinct paper title', '', '')
    monkeypatch.setattr(enrichment, 'download_public', lambda page, *_, **__: (
        page.replace('v1', 'v2'), '<title>A distinct paper title</title><article><img src="/figure.png"></article>'))
    assert enrichment.paper_illustrations(paper, '2611.12345v1') is None


def test_backfill_preserves_body_dates_review_and_creates_backup(tmp_path, monkeypatch):
    path = tmp_path / 'notes/cards/test.md'
    metadata = {'id': 'test', 'source_url': 'https://primary.example/story', 'title_en': 'Orion 3 release',
                'review_status': 'accepted', 'reviewed_by': 'teacher', 'news_dates': {'event': '2026-11-10'}}
    write_card(path, metadata, 'Existing reviewed article.')
    monkeypatch.setattr(enrichment, '_backfill_original', lambda _: None)
    monkeypatch.setattr(enrichment, 'enrich_news_sources', lambda llm, doc, *_, **__: doc)
    result = enrichment.enrich_saved_card(tmp_path, path, SimpleNamespace(available=False))
    current = read_card(path)
    assert result['added'] == 0 and current.content == 'Existing reviewed article.'
    assert current.metadata['news_dates'] == metadata['news_dates']
    assert current.metadata['reviewed_by'] == 'teacher' and current.metadata['review_status'] == 'accepted'
    assert read_card(tmp_path / 'data/backups/news-media-enrichment/notes/cards/test.md').metadata == metadata
