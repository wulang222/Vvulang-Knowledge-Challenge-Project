from datetime import UTC, datetime

import httpx2
import pytest

from ai_quiz.providers.base import PageFetchFailed
from ai_quiz.providers.web_sources import (
    PageExtractor,
    UnsafeUrlError,
    UrlSafetyPolicy,
    WebPageFetcher,
)


async def public_resolver(hostname: str) -> list[str]:
    assert hostname
    return ["93.184.216.34"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.1/private",
        "http://user:password@example.com/secret",
        "ftp://example.com/file",
    ],
)
async def test_url_policy_rejects_ssrf_and_unsupported_urls(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        await UrlSafetyPolicy(resolver=public_resolver).validate(url)


@pytest.mark.anyio
async def test_url_policy_accepts_public_http_and_https_urls() -> None:
    policy = UrlSafetyPolicy(resolver=public_resolver)

    assert await policy.validate("https://docs.example.edu/rag") == ("https://docs.example.edu/rag")


@pytest.mark.anyio
async def test_url_policy_rejects_hostname_resolving_to_private_address() -> None:
    async def private_resolver(hostname: str) -> list[str]:
        assert hostname == "evil.example"
        return ["192.168.1.2"]

    with pytest.raises(UnsafeUrlError, match="public address"):
        await UrlSafetyPolicy(resolver=private_resolver).validate("https://evil.example/path")


def test_page_extractor_removes_active_and_navigation_content() -> None:
    html = """
    <html><head>
      <title>RAG 官方指南</title>
      <meta property="og:site_name" content="Example University">
    </head><body>
      <nav>菜单不应进入正文</nav>
      <main><h1>RAG</h1><p>RAG 会先检索相关信息，再生成回答。</p></main>
      <script>stealSecrets()</script>
    </body></html>
    """

    page = PageExtractor().extract(
        url="https://docs.example.edu/rag",
        html=html,
        retrieved_at=datetime(2026, 10, 3, tzinfo=UTC),
    )

    assert page.title == "RAG 官方指南"
    assert page.publisher == "Example University"
    assert "RAG 会先检索相关信息" in page.content
    assert "菜单不应进入正文" not in page.content
    assert "stealSecrets" not in page.content


@pytest.mark.anyio
async def test_web_fetcher_reads_html_and_revalidates_redirects() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/start":
            return httpx2.Response(302, headers={"location": "/final"})
        return httpx2.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<html><title>指南</title><body><main>可靠正文</main></body></html>",
        )

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    fetcher = WebPageFetcher(
        client=client,
        safety_policy=UrlSafetyPolicy(resolver=public_resolver),
    )

    page = await fetcher.fetch("https://docs.example.edu/start")
    await fetcher.aclose()

    assert page.url == "https://docs.example.edu/final"
    assert page.title == "指南"
    assert page.content == "可靠正文"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("content_type", "body"),
    [("application/pdf", b"pdf"), ("text/html", b"x" * 20)],
)
async def test_web_fetcher_rejects_unsupported_or_oversized_content(
    content_type: str,
    body: bytes,
) -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        del request
        return httpx2.Response(200, headers={"content-type": content_type}, content=body)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    fetcher = WebPageFetcher(
        client=client,
        safety_policy=UrlSafetyPolicy(resolver=public_resolver),
        max_bytes=10,
    )

    with pytest.raises(PageFetchFailed):
        await fetcher.fetch("https://docs.example.edu/file")

    await fetcher.aclose()
