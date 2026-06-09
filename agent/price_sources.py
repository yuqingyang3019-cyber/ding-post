"""Fetch public commodity quotes from 100ppi.com."""

from __future__ import annotations

import argparse
import csv
import http.cookiejar
import logging
import os
import random
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from typing import Any

logger = logging.getLogger("ding-post.price_sources")

BASE_URL = "https://www.100ppi.com/mprice/mlist-1--{page}.html"
DEFAULT_PAGE_COUNT = 3
REQUEST_TIMEOUT = 15
PAGE_DELAY_SECONDS = 0.5
CHALLENGE_RETRY_COUNT = 3
CHALLENGE_RETRY_DELAY_SECONDS = (0.5, 0.9)
CACHE_TTL_SECONDS = int(os.getenv("PRICE_CACHE_TTL_SECONDS", "900"))
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.100ppi.com/",
}
_cached_report: dict[str, Any] | None = None
_cached_at = 0.0
HW_CHECK_VALUE_RE = re.compile(r'var _0x2 = "([^"]+)"')
CHALLENGE_MARKERS = ("HW_CHECK", "正在进行安全检查")
PRICE_RE = re.compile(r"^([\d.]+)(元/.+)$")

CSV_FIELDS = [
    "name",
    "spec",
    "brand",
    "price",
    "unit",
    "quoteType",
    "delivery",
    "trader",
    "publishedAt",
    "sourceUrl",
]


class QuoteTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_quote_table = False
        self._in_row = False
        self._in_cell = False
        self._current_cells: list[str] = []
        self._cell_parts: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        class_name = attrs_dict.get("class", "")

        if tag == "table" and "lp-table" in class_name:
            self._in_quote_table = True
            return

        if not self._in_quote_table:
            return

        if tag == "tr":
            self._in_row = True
            self._current_cells = []
            return

        if self._in_row and tag == "td":
            self._in_cell = True
            self._cell_parts = []
            title = attrs_dict.get("title", "").strip()
            if title:
                self._cell_parts.append(title)

    def handle_endtag(self, tag: str) -> None:
        if tag == "table" and self._in_quote_table:
            self._in_quote_table = False
            return

        if not self._in_quote_table:
            return

        if tag == "td" and self._in_cell:
            self._in_cell = False
            self._current_cells.append(_normalize_cell_text("".join(self._cell_parts)))
            return

        if tag == "tr" and self._in_row:
            self._in_row = False
            if len(self._current_cells) == 8:
                self.rows.append(self._current_cells)

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_parts.append(data)


def _normalize_cell_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("VIP", "")).strip()


def _parse_price_text(price_text: str) -> tuple[str, str]:
    match = PRICE_RE.match(price_text.replace(" ", ""))
    if not match:
        return price_text, ""
    return match.group(1), match.group(2)


def _extract_hw_check_value(html: str) -> str | None:
    match = HW_CHECK_VALUE_RE.search(html)
    if match:
        return match.group(1)
    return None


def _is_challenge_page(html: str) -> bool:
    return any(marker in html for marker in CHALLENGE_MARKERS)


class _QuoteFetcher:
    def __init__(self) -> None:
        self._cookie_jar = http.cookiejar.CookieJar()
        handlers: list[Any] = [
            urllib.request.HTTPCookieProcessor(self._cookie_jar),
            urllib.request.HTTPHandler(),
            urllib.request.HTTPSHandler(),
        ]
        proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
        if proxy_url:
            handlers.append(urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url}))
        self._opener = urllib.request.build_opener(*handlers)

    def fetch(self, page: int) -> str:
        url = BASE_URL.format(page=page)
        last_error = "100ppi 安全检查未通过"

        for attempt in range(1, CHALLENGE_RETRY_COUNT + 1):
            request = urllib.request.Request(url, headers=DEFAULT_HEADERS)
            with self._opener.open(request, timeout=REQUEST_TIMEOUT) as response:
                html = response.read().decode("utf-8", errors="replace")

            if not _is_challenge_page(html):
                return html

            cookie_value = _extract_hw_check_value(html)
            if not cookie_value:
                last_error = "100ppi 安全检查页面未返回 HW_CHECK cookie"
                break

            self._cookie_jar.set_cookie(
                http.cookiejar.Cookie(
                    version=0,
                    name="HW_CHECK",
                    value=cookie_value,
                    port=None,
                    port_specified=False,
                    domain=".100ppi.com",
                    domain_specified=True,
                    domain_initial_dot=True,
                    path="/",
                    path_specified=True,
                    secure=False,
                    expires=None,
                    discard=True,
                    comment=None,
                    comment_url=None,
                    rest={},
                    rfc2109=False,
                )
            )
            delay = random.uniform(*CHALLENGE_RETRY_DELAY_SECONDS)
            logger.info(
                "100ppi security check triggered on page %s, retry %s/%s after %.2fs",
                page,
                attempt,
                CHALLENGE_RETRY_COUNT,
                delay,
            )
            time.sleep(delay)
            last_error = "100ppi 安全检查未通过"

        raise RuntimeError(last_error)


def fetch_page_html(page: int, fetcher: _QuoteFetcher) -> str:
    return fetcher.fetch(page)


def parse_quote_rows(html: str) -> list[dict[str, str]]:
    parser = QuoteTableParser()
    parser.feed(html)
    quotes: list[dict[str, str]] = []

    for cells in parser.rows:
        price, unit = _parse_price_text(cells[3])
        quotes.append(
            {
                "name": cells[0],
                "spec": cells[1],
                "brand": cells[2],
                "price": price,
                "unit": unit,
                "quoteType": cells[4],
                "delivery": cells[5],
                "trader": cells[6],
                "publishedAt": cells[7],
            }
        )

    return quotes


def _dedupe_key(quote: dict[str, str]) -> tuple[str, ...]:
    return (
        quote["name"],
        quote["spec"],
        quote["brand"],
        quote["price"],
        quote["unit"],
        quote["delivery"],
        quote["publishedAt"],
    )


def dedupe_quotes(quotes: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, ...]] = set()
    deduped: list[dict[str, str]] = []

    for quote in quotes:
        key = _dedupe_key(quote)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(quote)

    return deduped


def fetch_100ppi_quotes(page_count: int = DEFAULT_PAGE_COUNT) -> list[dict[str, str]]:
    all_quotes: list[dict[str, str]] = []
    fetcher = _QuoteFetcher()

    for page in range(1, page_count + 1):
        if page > 1:
            time.sleep(PAGE_DELAY_SECONDS)

        html = fetch_page_html(page, fetcher)
        page_quotes = parse_quote_rows(html)
        if not page_quotes:
            raise RuntimeError(f"100ppi 第 {page} 页未解析到报价数据")

        source_url = BASE_URL.format(page=page)
        for quote in page_quotes:
            quote["sourceUrl"] = source_url
        all_quotes.extend(page_quotes)

    return dedupe_quotes(all_quotes)


def build_live_price_report(quotes: list[dict[str, str]]) -> dict[str, Any]:
    published_dates = [quote["publishedAt"] for quote in quotes if quote.get("publishedAt")]
    updated_at = max(published_dates) if published_dates else datetime.now().strftime("%Y-%m-%d")

    return {
        "updatedAt": updated_at,
        "sourceName": "生意社公开报价",
        "isFallback": False,
        "fallbackReason": "",
        "items": quotes,
    }


def get_price_report(fallback_data: dict[str, Any], page_count: int = DEFAULT_PAGE_COUNT) -> dict[str, Any]:
    global _cached_report, _cached_at

    now = time.time()
    if _cached_report and now - _cached_at < CACHE_TTL_SECONDS:
        logger.info("Using cached 100ppi price report")
        return _cached_report

    try:
        quotes = fetch_100ppi_quotes(page_count=page_count)
        if not quotes:
            raise RuntimeError("100ppi 未返回有效报价")
        logger.info("Loaded %s live quotes from 100ppi", len(quotes))
        report = build_live_price_report(quotes)
        _cached_report = report
        _cached_at = now
        return report
    except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
        reason = str(exc)
        logger.warning("Falling back to mock price data: %s", reason)
        return {
            **fallback_data,
            "sourceName": "缓存假数据",
            "isFallback": True,
            "fallbackReason": reason,
        }


def write_quotes_csv(quotes: list[dict[str, str]], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for quote in quotes:
            writer.writerow({field: quote.get(field, "") for field in CSV_FIELDS})


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch public quotes from 100ppi.com")
    parser.add_argument(
        "--pages",
        type=int,
        default=DEFAULT_PAGE_COUNT,
        help="number of pages to fetch (default: 3)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="optional CSV output path",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    quotes = fetch_100ppi_quotes(page_count=args.pages)
    print(f"Fetched {len(quotes)} quotes from 100ppi")

    if args.output:
        write_quotes_csv(quotes, args.output)
        print(f"Wrote CSV to {args.output}")


if __name__ == "__main__":
    main()
