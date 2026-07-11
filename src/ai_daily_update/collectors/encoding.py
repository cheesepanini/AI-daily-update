from __future__ import annotations

import requests


def fix_response_encoding(response: requests.Response) -> None:
    """Correct requests' encoding guess for HTML/text responses without a charset.

    Per RFC 2616, requests defaults text/* responses with no explicit
    charset parameter to ISO-8859-1. Many real-world servers omit the
    charset while actually serving UTF-8 (or another encoding declared only
    via a <meta charset> tag), so trusting that default mangles non-ASCII
    text such as Chinese titles into garbage. Fall back to requests'
    content-sniffing (apparent_encoding) whenever the header didn't specify
    a charset explicitly.
    """
    content_type = response.headers.get("content-type", "")
    if "charset=" in content_type.lower():
        return
    apparent = response.apparent_encoding
    if apparent:
        response.encoding = apparent
