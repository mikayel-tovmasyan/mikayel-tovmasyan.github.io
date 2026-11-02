#!/usr/bin/env python3
"""Check a static website without third-party packages or default network access.

Run from any directory:
    python scripts/check_site.py
    python scripts/check_site.py --base-url http://127.0.0.1:8000/

The optional HTTP pass checks local pages and their linked assets against a
running preview. External links are deliberately outside this check's scope.
"""

from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import mimetypes
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urljoin, urlsplit
from urllib.request import Request, urlopen


class Document(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.tags: Counter[str] = Counter()
        self.ids: Counter[str] = Counter()
        self.language = ""
        self.viewport = ""
        self.descriptions: list[str] = []
        self.titles: list[str] = []
        self.references: list[tuple[str, str, int]] = []
        self.issues: list[str] = []
        self._in_title = False
        self._title_parts: list[str] = []
        self._links: list[tuple[int, list[str], bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        line = self.getpos()[0]
        self.tags[tag] += 1
        if "id" in attributes:
            identifier = attributes["id"] or ""
            if not identifier:
                self.issues.append(f"line {line}: empty id")
            else:
                self.ids[identifier] += 1
        if tag == "html":
            self.language = attributes.get("lang") or ""
        elif tag == "title":
            self._in_title = True
            self._title_parts = []
        elif tag == "meta":
            name = (attributes.get("name") or "").lower()
            content = attributes.get("content") or ""
            if name == "viewport":
                self.viewport = content
            elif name == "description":
                self.descriptions.append(content.strip())
        if tag == "img" and "alt" not in attributes:
            self.issues.append(f"line {line}: image lacks an alt attribute")
        if tag == "img" and self._links:
            self._links[-1][1].append(attributes.get("alt") or "")
        if tag == "a":
            labelled = any((attributes.get(name) or "").strip()
                           for name in ("aria-label", "aria-labelledby", "title"))
            self._links.append((line, [], labelled))
            href = attributes.get("href")
            if href is None or not href.strip() or href.strip() == "#":
                self.issues.append(f"line {line}: link has no usable destination")
            if (attributes.get("target") or "").lower() == "_blank":
                rel = (attributes.get("rel") or "").lower().split()
                if "noopener" not in rel:
                    self.issues.append(f"line {line}: target=_blank lacks rel=noopener")
        for name in ("href", "src"):
            if name in attributes:
                value = attributes[name] or ""
                if name == "src" and not value.strip():
                    self.issues.append(f"line {line}: empty src attribute")
                elif value.strip():
                    self.references.append((name, value.strip(), line))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self.titles.append(" ".join("".join(self._title_parts).split()))
            self._in_title = False
        if tag == "a" and self._links:
            line, text, labelled = self._links.pop()
            if not labelled and not "".join(text).strip():
                self.issues.append(f"line {line}: link has no text or accessible label")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        for _line, text, _labelled in self._links:
            text.append(data)


def read_document(path: Path) -> Document:
    document = Document(path)
    document.feed(path.read_text(encoding="utf-8"))
    document.close()
    return document


def resolve_local(root: Path, source: Path, value: str) -> tuple[Path, str] | None:
    """Resolve site-relative references, leaving external schemes untouched."""
    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        return None
    url_path = unquote(parts.path)
    if not url_path:
        target = source
    elif url_path.startswith("/"):
        target = root / url_path.lstrip("/")
    else:
        target = source.parent / url_path
    target = target.resolve()
    if not target.is_relative_to(root):
        raise ValueError("destination escapes the website directory")
    if target.is_dir():
        target = target / "index.html"
    return target, unquote(parts.fragment)


def expected_content_type(path: Path) -> str | None:
    # Explicit types avoid differences between OS MIME registries.
    common = {
        ".html": "text/html", ".htm": "text/html", ".css": "text/css",
        ".pdf": "application/pdf", ".svg": "image/svg+xml",
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".ico": "image/", ".json": "application/json",
    }
    return common.get(path.suffix.lower(), mimetypes.guess_type(path.name)[0])


def http_check(root: Path, files: set[Path], base_url: str, errors: list[str]) -> int:
    base = base_url.rstrip("/") + "/"
    count = 0
    for path in sorted(files):
        relative = path.relative_to(root).as_posix()
        url = urljoin(base, quote(relative))
        try:
            request = Request(url, headers={"User-Agent": "StaticSiteCheck/1.0"})
            with urlopen(request, timeout=15) as response:
                count += 1
                if not 200 <= response.status < 300:
                    errors.append(f"HTTP {relative}: unexpected status {response.status}")
                actual = response.headers.get_content_type().lower()
                expected = expected_content_type(path)
                if path.suffix.lower() in {".js", ".mjs"}:
                    matches = actual in {"text/javascript", "application/javascript"}
                elif expected == "image/":
                    matches = actual.startswith(expected)
                else:
                    matches = expected is None or actual == expected
                if not matches:
                    errors.append(f"HTTP {relative}: type {actual!r}, expected {expected!r}")
                if path.suffix.lower() == ".pdf" and response.read(5) != b"%PDF-":
                    errors.append(f"HTTP {relative}: response is not a PDF")
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            errors.append(f"HTTP {relative}: {error}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent,
                        help="Website root (default: the parent of scripts/)")
    parser.add_argument("--base-url", help="Also validate HTTP responses from this preview URL")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.base_url and urlsplit(args.base_url).scheme not in {"http", "https"}:
        parser.error("--base-url must begin with http:// or https://")
    html_files = sorted(path for path in root.rglob("*.html")
                        if not any(part.startswith(".") for part in path.relative_to(root).parts))
    errors: list[str] = []
    documents: dict[Path, Document] = {}
    checked_files: set[Path] = set(html_files)
    if not html_files:
        errors.append("No HTML pages found")
    for path in html_files:
        label = path.relative_to(root).as_posix()
        try:
            doc = read_document(path)
        except (OSError, UnicodeError) as error:
            errors.append(f"{label}: cannot read UTF-8 HTML: {error}")
            continue
        documents[path] = doc
        errors.extend(f"{label}: {issue}" for issue in doc.issues)
        if not re.fullmatch(r"en(?:-[A-Za-z0-9]+)*", doc.language, re.IGNORECASE):
            errors.append(f"{label}: missing or non-English html lang attribute")
        if "width=device-width" not in doc.viewport.replace(" ", "").lower():
            errors.append(f"{label}: missing responsive viewport metadata")
        if len(doc.titles) != 1 or not doc.titles[0]:
            errors.append(f"{label}: expected one nonempty title")
        if len(doc.descriptions) != 1 or not doc.descriptions[0]:
            errors.append(f"{label}: expected one nonempty meta description")
        for landmark in ("h1", "main"):
            if doc.tags[landmark] != 1:
                errors.append(f"{label}: expected one {landmark}, found {doc.tags[landmark]}")
        for landmark in ("header", "nav", "footer"):
            if not doc.tags[landmark]:
                errors.append(f"{label}: missing {landmark} landmark")
        for identifier, count in doc.ids.items():
            if count > 1:
                errors.append(f"{label}: duplicate id {identifier!r} ({count} occurrences)")
    for field in ("titles", "descriptions"):
        seen: dict[str, str] = {}
        for path, doc in documents.items():
            label = path.relative_to(root).as_posix()
            values = getattr(doc, field)
            if len(values) == 1 and values[0]:
                key = values[0].casefold()
                if key in seen:
                    errors.append(f"{label}: {field[:-1]} duplicates {seen[key]}")
                seen[key] = label

    references = [(path, value, f"line {line}") for path, doc in documents.items()
                  for _attribute, value, line in doc.references]
    # Include CSS images/fonts referenced through url(), without fetching externals.
    checked_css: set[Path] = set()
    index = 0
    while index < len(references):
        source, value, location = references[index]
        index += 1
        label = source.relative_to(root).as_posix()
        try:
            resolved = resolve_local(root, source, value)
        except ValueError as error:
            errors.append(f"{label} {location}: {value!r}: {error}")
            continue
        if resolved is None:
            continue
        target, fragment = resolved
        if not target.is_file():
            errors.append(f"{label} {location}: missing local destination {value!r}")
            continue
        checked_files.add(target)
        if fragment and target.suffix.lower() in {".html", ".htm", ".svg"}:
            try:
                target_doc = documents.get(target) or read_document(target)
                if fragment not in target_doc.ids:
                    errors.append(f"{label} {location}: missing fragment in {value!r}")
            except (OSError, UnicodeError) as error:
                errors.append(f"{label}: cannot inspect fragment target: {error}")
        if target.suffix.lower() == ".css" and target not in checked_css:
            checked_css.add(target)
            try:
                css = re.sub(r"/\*.*?\*/", "", target.read_text(encoding="utf-8"), flags=re.DOTALL)
                for match in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)", css, re.IGNORECASE):
                    references.append((target, match.group(2).strip(), "CSS url()"))
            except (OSError, UnicodeError) as error:
                errors.append(f"{label}: cannot inspect stylesheet: {error}")
    for path in checked_files:
        if path.suffix.lower() == ".pdf":
            with path.open("rb") as pdf:
                if pdf.read(5) != b"%PDF-":
                    errors.append(f"{path.relative_to(root)}: invalid PDF signature")
    http_count = http_check(root, checked_files, args.base_url, errors) if args.base_url else 0
    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    suffix = f"; {http_count} HTTP responses checked" if args.base_url else "; network not used"
    print(f"PASS: {len(documents)} HTML pages; {len(checked_files)} local files verified{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
