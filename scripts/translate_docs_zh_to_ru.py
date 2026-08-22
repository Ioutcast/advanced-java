#!/usr/bin/env python3
"""Translate all Markdown files under docs/ from Chinese to Russian.

Preserves Markdown/HTML structure (code fences, inline code, links, images,
HTML blocks) and translates coherent paragraph-sized chunks for readable text.
Supports resume via a simple progress JSON file.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

from deep_translator import GoogleTranslator
from deep_translator.exceptions import RequestError, TooManyRequests

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
PROGRESS_PATH = ROOT / "scripts" / ".translate_docs_progress.json"
MAX_CHUNK = 1000
RETRY_SLEEP = 4.0
MAX_RETRIES = 10
REQUEST_PAUSE = 0.65

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
CYR_RE = re.compile(r"[\u0400-\u04FF]")

# Protect structural Markdown / HTML fragments from translation.
PROTECT_PATTERNS = [
    re.compile(r"```[\s\S]*?```"),  # fenced code
    re.compile(r"`[^`\n]+`"),  # inline code
    re.compile(r"!\[[^\]]*\]\([^)]+\)"),  # images
    re.compile(r"\[[^\]]*\]\([^)]+\)"),  # links (keep URL; translate label separately below)
    re.compile(r"<pre[\s\S]*?</pre>", re.I),
    re.compile(r"<code[\s\S]*?</code>", re.I),
    re.compile(r"<script[\s\S]*?</script>", re.I),
    re.compile(r"<style[\s\S]*?</style>", re.I),
    re.compile(r"<iframe[\s\S]*?</iframe>", re.I),
    re.compile(r"</?[a-zA-Z][^>]*>"),  # keep HTML tags; translate text between them
    re.compile(r"https?://[^\s)>\]]+"),
    re.compile(r"\[[^\]]+\]:\s*\S+"),  # reference-style link defs
]

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

# Prefer stable technical terms (longer phrases first).
# Applied before machine translation so Google keeps the English token.
GLOSSARY = [
    ("分库分表", "database sharding"),
    ("读写分离", "read/write splitting"),
    ("缓存雪崩", "cache avalanche"),
    ("缓存穿透", "cache penetration"),
    ("缓存击穿", "cache breakdown"),
    ("布隆过滤器", "Bloom filter"),
    ("消息队列", "message queue"),
    ("分布式锁", "distributed lock"),
    ("分布式事务", "distributed transaction"),
    ("题目描述", "Problem statement"),
    ("解答思路", "Solution approach"),
    ("方法总结", "Summary"),
    ("微服务", "microservices"),
    ("高并发", "high concurrency"),
    ("高可用", "high availability"),
    ("限流", "rate limiting"),
    ("熔断", "circuit breaker"),
    ("降级", "fallback"),
    ("幂等", "idempotent"),
    ("主从复制", "master-slave replication"),
    ("哨兵", "Sentinel"),
    ("位图法", "bitmap method"),
    ("位图", "bitmap"),
    ("红黑树", "red-black tree"),
    ("面试题剖析", "Interview question analysis"),
    ("面试题", "Interview question"),
    ("面试官心理分析", "What the interviewer wants to know"),
    ("面试官", "Interviewer"),
    ("公众号", "WeChat official account"),
]
GLOSSARY.sort(key=lambda x: len(x[0]), reverse=True)

# Fix frequent awkward machine-translation leftovers.
POST_FIXES = [
    (
        re.compile(
            r"растров(?:ого|ом|ый|ая|ые|ых|ым|ому|ое|ую)?\s+изображени\w*",
            re.I,
        ),
        "bitmap",
    ),
    (re.compile(r"растров(?:ый|ого|ом|ая|ые|ым|ое)?\s+метод\w*", re.I), "bitmap-метод"),
    (re.compile(r"метод\s+растров\w*", re.I), "bitmap-метод"),
    (re.compile(r"в\s+растров\w*\s+изображени\w*", re.I), "в bitmap"),
]



def apply_glossary(text: str) -> str:
    for zh, en in GLOSSARY:
        text = text.replace(zh, en)
    return text


def apply_post_fixes(text: str) -> str:
    for pattern, repl in POST_FIXES:
        text = pattern.sub(repl, text)
    return text


def file_key(path: Path) -> str:
    return str(path.relative_to(DOCS_DIR)).replace("\\", "/")


def load_progress() -> dict:
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    return {"done": {}}


def save_progress(progress: dict) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def content_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def needs_translation(text: str) -> bool:
    cjk = len(CJK_RE.findall(text))
    if cjk < 8:
        return False
    cyr = len(CYR_RE.findall(text))
    # Already mostly Russian
    if cyr > cjk * 2:
        return False
    return True


def protect(text: str) -> tuple[str, list[str]]:
    vault: list[str] = []

    def stash(match: re.Match) -> str:
        vault.append(match.group(0))
        return f"⟦P{len(vault) - 1}⟧"

    out = text
    for pattern in PROTECT_PATTERNS:
        out = pattern.sub(stash, out)
    return out, vault


def restore(text: str, vault: list[str]) -> str:
    def unstash(match: re.Match) -> str:
        idx = int(match.group(1))
        return vault[idx]

    return re.sub(r"⟦P(\d+)⟧", unstash, text)


def split_chunks(text: str, max_len: int = MAX_CHUNK) -> list[str]:
    """Split into coherent chunks on blank lines / headings when possible."""
    if len(text) <= max_len:
        return [text]

    parts = re.split(r"(\n\s*\n)", text)  # keep separators
    chunks: list[str] = []
    buf = ""

    def flush() -> None:
        nonlocal buf
        if buf:
            chunks.append(buf)
            buf = ""

    for part in parts:
        if not part:
            continue
        if len(buf) + len(part) <= max_len:
            buf += part
            continue
        flush()
        if len(part) <= max_len:
            buf = part
            continue
        # Hard-split long blocks by lines, then by size
        lines = part.split("\n")
        for line in lines:
            piece = line + "\n"
            if len(buf) + len(piece) <= max_len:
                buf += piece
            else:
                flush()
                if len(piece) <= max_len:
                    buf = piece
                else:
                    for i in range(0, len(piece), max_len):
                        chunks.append(piece[i : i + max_len])
                    buf = ""
    flush()
    return chunks or [text]


def translate_raw(text: str, translator: GoogleTranslator) -> str:
    text = text.strip("\n")
    if not text or not CJK_RE.search(text):
        return text

    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Google free endpoint rejects empty / whitespace-only
            translated = translator.translate(text)
            if translated is None:
                return text
            return translated
        except TooManyRequests as exc:
            last_err = exc
            sleep_for = RETRY_SLEEP * attempt * 2
            print(f"  rate-limited, sleep {sleep_for:.1f}s...", flush=True)
            time.sleep(sleep_for)
        except (RequestError, Exception) as exc:  # noqa: BLE001
            last_err = exc
            sleep_for = RETRY_SLEEP * attempt
            print(f"  translate error ({exc}), retry in {sleep_for:.1f}s", flush=True)
            time.sleep(sleep_for)
    raise RuntimeError(f"Failed to translate after retries: {last_err}")


def translate_link_labels(text: str, translator: GoogleTranslator) -> str:
    """Translate Chinese labels inside [label](url) / ![alt](url)."""

    def repl_link(match: re.Match, is_image: bool = False) -> str:
        label, url = match.group(1), match.group(2)
        if CJK_RE.search(label):
            label = translate_raw(label, translator)
        prefix = "!" if is_image else ""
        return f"{prefix}[{label}]({url})"

    text = IMAGE_RE.sub(lambda m: repl_link(m, True), text)
    text = LINK_RE.sub(lambda m: repl_link(m, False), text)
    return text


def translate_markdown(text: str, translator: GoogleTranslator) -> str:
    # First pass: translate link/image labels while URLs intact
    # Do this before protecting whole links, so labels get translated.
    # We temporarily protect code so labels inside code are not touched.
    code_vault: list[str] = []

    def stash_code(match: re.Match) -> str:
        code_vault.append(match.group(0))
        return f"⟦C{len(code_vault) - 1}⟧"

    working = re.compile(r"```[\s\S]*?```").sub(stash_code, text)
    working = re.compile(r"`[^`\n]+`").sub(stash_code, working)
    working = apply_glossary(working)
    working = translate_link_labels(working, translator)

    def unstash_code(match: re.Match) -> str:
        return code_vault[int(match.group(1))]

    working = re.sub(r"⟦C(\d+)⟧", unstash_code, working)

    protected, vault = protect(working)
    chunks = split_chunks(protected)
    out_parts: list[str] = []
    for i, chunk in enumerate(chunks):
        if not CJK_RE.search(chunk):
            out_parts.append(chunk)
            continue
        # Preserve leading/trailing newlines around the translated body
        lead = re.match(r"^\n*", chunk).group(0)
        trail = re.search(r"\n*$", chunk).group(0)
        body = chunk[len(lead) : len(chunk) - len(trail) if trail else len(chunk)]
        if not body:
            out_parts.append(chunk)
            continue
        translated = translate_raw(body, translator)
        out_parts.append(lead + translated + trail)
        time.sleep(REQUEST_PAUSE)
        if (i + 1) % 10 == 0:
            print(f"    chunk {i + 1}/{len(chunks)}", flush=True)

    restored = restore("".join(out_parts), vault)
    return apply_post_fixes(restored)

def translate_file(path: Path, translator: GoogleTranslator) -> bool:
    original = path.read_text(encoding="utf-8")
    if not needs_translation(original):
        print(f"SKIP (no ZH / already RU): {file_key(path)}", flush=True)
        return False

    print(f"TRANSLATE: {file_key(path)} ({len(original)} chars)", flush=True)
    translated = translate_markdown(original, translator)

    # Safety: if translation somehow emptied content, abort write
    if len(translated.strip()) < max(20, len(original.strip()) // 20):
        raise RuntimeError(f"Suspicious short translation for {path}")

    # Python 3.8: Path.write_text has no newline=; normalize manually.
    normalized = translated.replace("\r\n", "\n").replace("\r", "\n")
    path.write_text(normalized, encoding="utf-8")
    return True


def main() -> int:
    if not DOCS_DIR.is_dir():
        print(f"Docs dir not found: {DOCS_DIR}", file=sys.stderr)
        return 1

    files = sorted(DOCS_DIR.rglob("*.md"))
    progress = load_progress()
    translator = GoogleTranslator(source="zh-CN", target="ru")

    done = 0
    skipped = 0
    failed: list[str] = []

    for path in files:
        key = file_key(path)
        text = path.read_text(encoding="utf-8")
        if not needs_translation(text):
            skipped += 1
            continue
        # Resume: already successfully processed this exact content
        prev = progress["done"].get(key)
        if prev and prev.get("hash_before") == content_hash(text) and prev.get("ok"):
            skipped += 1
            continue

        try:
            before = text
            changed = translate_file(path, translator)
            after = path.read_text(encoding="utf-8")
            progress["done"][key] = {
                "hash_before": content_hash(before),
                "hash_after": content_hash(after),
                "changed": changed,
                "ok": True,
            }
            save_progress(progress)
            if changed:
                done += 1
            else:
                skipped += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: {key}: {exc}", flush=True)
            failed.append(key)
            progress["done"][key] = {
                "hash_before": content_hash(text),
                "ok": False,
                "error": str(exc),
            }
            save_progress(progress)
            time.sleep(2)

    print(
        f"\nFinished. translated={done} skipped={skipped} failed={len(failed)}",
        flush=True,
    )
    if failed:
        print("Failed files:", flush=True)
        for f in failed:
            print(f"  - {f}", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
