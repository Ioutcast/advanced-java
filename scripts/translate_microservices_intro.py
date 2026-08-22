#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translate a single large Markdown file in small section/paragraph chunks."""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

from deep_translator import GoogleTranslator
from deep_translator.exceptions import RequestError, TooManyRequests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translate_docs_zh_to_ru as m  # noqa: E402

PATH = Path(r"e:/advanced-java/docs/micro-services/microservices-introduction.md")
CHUNK = 1000
PAUSE = 0.65
MAX_RETRIES = 12


def split_by_headings(text: str) -> list[str]:
    parts = re.split(r"(?m)(?=^#{1,3} )", text)
    return [p for p in parts if p]


def hard_chunks(text: str, max_len: int) -> list[str]:
    if len(text) <= max_len:
        return [text]
    paras = re.split(r"(\n\s*\n)", text)
    out: list[str] = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) <= max_len:
            buf += p
            continue
        if buf:
            out.append(buf)
            buf = ""
        if len(p) <= max_len:
            buf = p
            continue
        for line in p.splitlines(keepends=True):
            if len(buf) + len(line) <= max_len:
                buf += line
            else:
                if buf:
                    out.append(buf)
                if len(line) <= max_len:
                    buf = line
                else:
                    for i in range(0, len(line), max_len):
                        out.append(line[i : i + max_len])
                    buf = ""
    if buf:
        out.append(buf)
    return out or [text]


def translate_body(body: str, tr: GoogleTranslator) -> str:
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            translated = tr.translate(body)
            return body if translated is None else translated
        except (TooManyRequests, RequestError, Exception) as exc:  # noqa: BLE001
            last = exc
            sleep = min(60, 2.5 * attempt)
            print(f"    retry {attempt}/{MAX_RETRIES}: {exc}; sleep {sleep:.1f}s", flush=True)
            time.sleep(sleep)
    raise RuntimeError(f"chunk failed after retries: {last}")


def translate_section(text: str, tr: GoogleTranslator) -> str:
    code_vault: list[str] = []

    def stash_code(match: re.Match) -> str:
        code_vault.append(match.group(0))
        return f"⟦C{len(code_vault) - 1}⟧"

    working = re.compile(r"```[\s\S]*?```").sub(stash_code, text)
    working = re.compile(r"`[^`\n]+`").sub(stash_code, working)
    working = m.apply_glossary(working)
    working = m.translate_link_labels(working, tr)
    working = re.sub(r"⟦C(\d+)⟧", lambda mo: code_vault[int(mo.group(1))], working)

    protected, vault = m.protect(working)
    pieces = hard_chunks(protected, CHUNK)
    out: list[str] = []
    for i, chunk in enumerate(pieces):
        if not m.CJK_RE.search(chunk):
            out.append(chunk)
            continue
        lead = re.match(r"^\n*", chunk).group(0)
        trail = re.search(r"\n*$", chunk).group(0)
        end = len(chunk) - len(trail) if trail else len(chunk)
        body = chunk[len(lead) : end]
        if not body.strip():
            out.append(chunk)
            continue
        translated = translate_body(body, tr)
        out.append(lead + translated + trail)
        time.sleep(PAUSE)
        print(f"    piece {i + 1}/{len(pieces)} ok ({len(body)} chars)", flush=True)

    restored = m.restore("".join(out), vault)
    return m.apply_post_fixes(restored)


def main() -> int:
    if not PATH.exists():
        print(f"missing: {PATH}", file=sys.stderr)
        return 1

    original = PATH.read_text(encoding="utf-8")
    if not m.needs_translation(original):
        print("Already translated / no Chinese left")
        return 0

    sections = split_by_headings(original)
    print(f"sections={len(sections)} total_chars={len(original)}", flush=True)

    checkpoint = PATH.with_suffix(".md.partial.ru")
    prog = PATH.with_suffix(".md.partial.idx")
    start_idx = int(prog.read_text(encoding="utf-8").strip()) if prog.exists() else 0

    if start_idx > 0 and checkpoint.exists():
        result_parts = [checkpoint.read_text(encoding="utf-8")]
        print(f"Resuming at section index {start_idx}", flush=True)
    else:
        start_idx = 0
        result_parts = []

    tr = GoogleTranslator(source="zh-CN", target="ru")

    for idx in range(start_idx, len(sections)):
        sec = sections[idx]
        preview = sec.strip().splitlines()[0][:80] if sec.strip() else "(empty)"
        print(f"SECTION {idx + 1}/{len(sections)}: {preview}", flush=True)
        translated = translate_section(sec, tr) if m.CJK_RE.search(sec) else sec
        result_parts.append(translated)
        joined = "".join(result_parts)
        checkpoint.write_text(joined, encoding="utf-8")
        prog.write_text(str(idx + 1), encoding="utf-8")
        print(f"  checkpoint saved ({len(joined)} chars)", flush=True)

    final = m.apply_post_fixes("".join(result_parts)).replace("\r\n", "\n").replace("\r", "\n")
    PATH.write_text(final, encoding="utf-8")
    if checkpoint.exists():
        checkpoint.unlink()
    if prog.exists():
        prog.unlink()

    left = len(m.CJK_RE.findall(final))
    print(f"DONE. chars={len(final)} remaining_cjk={left}", flush=True)
    return 0 if left < 40 else 2


if __name__ == "__main__":
    raise SystemExit(main())
