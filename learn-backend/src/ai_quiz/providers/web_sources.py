"""SSRF-aware public page retrieval and deterministic HTML extraction."""

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx2
from bs4 import BeautifulSoup

from ai_quiz.providers.base import FetchedPage, PageFetchFailed

Resolver = Callable[[str], Awaitable[list[str]]]


class UnsafeUrlError(ValueError):
    pass


async def resolve_public_addresses(hostname: str) -> list[str]:
    def resolve() -> list[str]:
        records = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        return sorted({str(record[4][0]) for record in records})

    return await asyncio.to_thread(resolve)


class UrlSafetyPolicy:
    def __init__(self, *, resolver: Resolver = resolve_public_addresses) -> None:
        self._resolver = resolver

    async def validate(self, url: str) -> str:
        try:
            parsed = urlsplit(url)
            port = parsed.port
        except ValueError as exc:
            raise UnsafeUrlError("URL is malformed") from exc
        if parsed.scheme not in {"http", "https"}:
            raise UnsafeUrlError("URL scheme is not allowed")
        if parsed.username or parsed.password:
            raise UnsafeUrlError("URL credentials are not allowed")
        if not parsed.hostname:
            raise UnsafeUrlError("URL hostname is required")
        if port is not None and not 1 <= port <= 65535:
            raise UnsafeUrlError("URL port is invalid")

        hostname = parsed.hostname.rstrip(".").casefold()
        if hostname == "localhost" or hostname.endswith(".localhost"):
            raise UnsafeUrlError("URL must resolve to a public address")
        try:
            addresses = [hostname] if self._is_ip(hostname) else await self._resolver(hostname)
        except (OSError, socket.gaierror) as exc:
            raise UnsafeUrlError("URL hostname cannot be resolved") from exc
        if not addresses or any(
            not ipaddress.ip_address(address).is_global for address in addresses
        ):
            raise UnsafeUrlError("URL must resolve to a public address")

        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))

    @staticmethod
    def _is_ip(hostname: str) -> bool:
        try:
            ipaddress.ip_address(hostname)
        except ValueError:
            return False
        return True


class PageExtractor:
    def extract(self, *, url: str, html: str, retrieved_at: datetime) -> FetchedPage:
        soup = BeautifulSoup(html, "html.parser")
        for node in soup.select("script, style, noscript, nav, footer, header, form, iframe"):
            node.decompose()
        title = self._meta(soup, "og:title") or (
            soup.title.get_text(" ", strip=True) if soup.title else urlsplit(url).hostname or url
        )
        publisher = self._meta(soup, "og:site_name") or urlsplit(url).hostname or "未知发布方"
        container = soup.find("main") or soup.find("article") or soup.body or soup
        lines = [line.strip() for line in container.get_text("\n").splitlines() if line.strip()]
        content = "\n".join(lines)
        if not content:
            raise PageFetchFailed(url)
        return FetchedPage(
            url=url,
            title=title[:300],
            publisher=publisher[:200],
            content=content,
            retrieved_at=retrieved_at,
        )

    @staticmethod
    def _meta(soup: BeautifulSoup, property_name: str) -> str | None:
        node = soup.find("meta", attrs={"property": property_name})
        if node is None:
            return None
        value = node.get("content")
        return value.strip() if isinstance(value, str) and value.strip() else None


class WebPageFetcher:
    def __init__(
        self,
        *,
        client: httpx2.AsyncClient,
        safety_policy: UrlSafetyPolicy | None = None,
        extractor: PageExtractor | None = None,
        max_bytes: int = 2_000_000,
        max_redirects: int = 3,
    ) -> None:
        self._client = client
        self._safety_policy = safety_policy or UrlSafetyPolicy()
        self._extractor = extractor or PageExtractor()
        self._max_bytes = max_bytes
        self._max_redirects = max_redirects

    async def fetch(self, url: str) -> FetchedPage:
        current_url = url
        try:
            for redirect_count in range(self._max_redirects + 1):
                current_url = await self._safety_policy.validate(current_url)
                response = await self._client.get(current_url, follow_redirects=False)
                if response.is_redirect:
                    if redirect_count == self._max_redirects:
                        raise PageFetchFailed(current_url)
                    location = response.headers.get("location")
                    if not location:
                        raise PageFetchFailed(current_url)
                    current_url = urljoin(current_url, location)
                    continue
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").casefold()
                if "text/html" not in content_type and "text/plain" not in content_type:
                    raise PageFetchFailed(current_url)
                if len(response.content) > self._max_bytes:
                    raise PageFetchFailed(current_url)
                return self._extractor.extract(
                    url=current_url,
                    html=response.text,
                    retrieved_at=datetime.now(UTC),
                )
        except (httpx2.HTTPError, UnsafeUrlError, UnicodeError) as exc:
            raise PageFetchFailed(current_url) from exc
        raise PageFetchFailed(current_url)

    async def aclose(self) -> None:
        await self._client.aclose()
