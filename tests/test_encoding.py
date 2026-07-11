import requests
from requests.utils import get_encoding_from_headers

from ai_daily_update.collectors.encoding import fix_response_encoding


def _response(content_type: str, body_bytes: bytes) -> requests.Response:
    # Mirrors what requests.adapters.HTTPAdapter.build_response does: set
    # .encoding from the Content-Type header before the body is available
    # via .text.
    response = requests.models.Response()
    response.status_code = 200
    response.headers["content-type"] = content_type
    response._content = body_bytes
    response.encoding = get_encoding_from_headers(response.headers)
    return response


def test_fix_response_encoding_corrects_missing_charset_utf8() -> None:
    body = "<html><title>中文标题</title></html>".encode("utf-8")
    response = _response("text/html", body)
    assert response.encoding == "ISO-8859-1"
    assert "中文标题" not in response.text

    fix_response_encoding(response)

    assert "中文标题" in response.text


def test_fix_response_encoding_leaves_explicit_charset_alone() -> None:
    body = "<html><title>hello</title></html>".encode("utf-8")
    response = _response("text/html; charset=utf-8", body)

    fix_response_encoding(response)

    assert response.encoding == "utf-8"
