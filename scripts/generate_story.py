#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime
from typing import List


def read_story_seed(path: str) -> dict:
    """
    Read a simple seed file. Expected loose format:
      題名: <title>
      あらすじ: <one or more lines>
    Fallback: first non-empty line as title, rest as synopsis.
    """
    title = None
    synopsis_lines = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f]
    for ln in lines:
        if not ln.strip():
            continue
        if title is None and (ln.startswith('題名:') or ln.lower().startswith('title:')):
            title = ln.split(':', 1)[1].strip()
            continue
        if ln.startswith('あらすじ:') or ln.lower().startswith('synopsis:'):
            synopsis_lines.append(ln.split(':', 1)[1].strip())
            continue
        if title is None:
            title = ln.strip()
        else:
            synopsis_lines.append(ln)
    if title is None:
        title = os.path.splitext(os.path.basename(path))[0]
    synopsis = '\n'.join([s for s in synopsis_lines if s.strip()]) or '短いお話を子ども向けにまとめてください。'
    return {"title": title, "synopsis": synopsis}


def build_marp_from_gemini(title: str, synopsis: str, model_name: str, api_key: str) -> str:
    """
    Use Google Gemini to generate Marp-compatible Markdown slides.
    If the library or API fails, raise and let caller fallback.
    """
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    system_preamble = (
        "You are a children picture-book writer and editor. "
        "Generate concise Japanese text suitable for picture-book slides. "
        "Keep sentences short and friendly."
    )
    user_prompt = f'''次の題名とあらすじから、Marp対応のMarkdownスライドを生成してください。
- スライド1: タイトルだけ大きく（著者名は省略可）
- スライド2以降: 1枚に2〜5行、やさしい短文で。
- 最後のスライド: おわり と ひとこと（前向きな締め）
- 画像は入れない（テキストのみ）
- 出力にはMarpフロントマターを必ず含める（marp: true, title, paginate: true）。

題名: {title}
あらすじ:
{synopsis}
'''
    res = model.generate_content([
        {"role": "system", "parts": system_preamble},
        {"role": "user", "parts": user_prompt},
    ])
    text = getattr(res, 'text', None) or (res.candidates[0].content.parts[0].text if getattr(res, 'candidates', None) else None)
    if not text:
        raise RuntimeError('Empty response from Gemini')
    return text


def build_marp_template(title: str, synopsis: str) -> str:
    now = datetime.utcnow().strftime('%Y-%m-%d')
    return f'''---
marp: true
title: {title}
paginate: true
theme: default
---

# {title}

---
# はじまり

{synopsis}

---
# つづき

- 1つめの出来事
- 2つめの出来事
- 3つめの出来事

---
# おわりに

読んでくれてありがとう！
({now})
'''


def _split_slides(marp_md: str) -> List[str]:
    # Split by slide delimiter '---' while keeping content grouped
    parts: List[str] = []
    current: List[str] = []
    for line in marp_md.splitlines():
        if line.strip() == '---':
            if current:
                parts.append('\n'.join(current).strip('\n'))
                current = []
            parts.append('---')  # delimiter marker
        else:
            current.append(line)
    if current:
        parts.append('\n'.join(current).strip('\n'))
    # Reconstruct slides: first chunk is frontmatter block, then alternating delimiter/content
    slides: List[str] = []
    buf: List[str] = []
    for chunk in parts:
        if chunk == '---':
            if buf:
                slides.append('\n'.join(buf).strip('\n'))
                buf = []
        else:
            buf.append(chunk)
    if buf:
        slides.append('\n'.join(buf).strip('\n'))
    return slides


def _first_text_line(block: str) -> str:
    for ln in block.splitlines():
        s = ln.strip().lstrip('#').strip()
        if s:
            return s[:40]
    return ''


def _write_svg(path: str, text: str, index: int) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Simple colorful background with centered text
    palette = ["#FFEDD5", "#E0F2FE", "#ECFCCB", "#FCE7F3", "#FEF9C3"]
    bg = palette[index % len(palette)]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="#ffffff"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#g)"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="48" font-family="'Segoe UI', 'Noto Sans JP', sans-serif" fill="#333">{text}</text>
</svg>'''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(svg)


def embed_placeholders_and_images(marp_md: str, out_md_path: str) -> str:
    """
    Generate simple SVG placeholders per content slide and embed image tags
    at the top of each slide (except the very first title slide).
    Images are saved under slides/images relative to out_md_path.
    """
    slides = _split_slides(marp_md)
    if not slides:
        return marp_md
    md_dir = os.path.dirname(out_md_path)
    images_dir = os.path.join(md_dir, 'images')
    new_slides: List[str] = []
    for idx, slide in enumerate(slides):
        if idx == 0:
            # keep frontmatter/title slide as-is
            new_slides.append(slide)
            continue
        label = _first_text_line(slide) or f'Slide {idx+1}'
        img_name = f'slide-{idx+1}.svg'
        img_path = os.path.join(images_dir, img_name)
        _write_svg(img_path, label, idx)
        # Prepend image markdown
        rel = f'images/{img_name}'
        augmented = f'![illustration]({rel})\n\n{slide}'.strip()
        new_slides.append(augmented)
    # Reassemble with separators
    return ('\n---\n\n').join(new_slides).strip() + '\n'


def main():
    p = argparse.ArgumentParser(description='Generate Marp Markdown story from a seed text via Gemini (fallback to template).')
    p.add_argument('--input', required=True, help='Path to story seed text (UTF-8).')
    p.add_argument('--out', required=True, help='Output path for Marp Markdown.')
    p.add_argument('--model', default='gemini-1.5-flash', help='Gemini model name (default: gemini-1.5-flash).')
    args = p.parse_args()

    seed = read_story_seed(args.input)
    title = seed['title']
    synopsis = seed['synopsis']

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    api_key = os.getenv('GEMINI_API_KEY')
    content = None
    if api_key:
        try:
            content = build_marp_from_gemini(title, synopsis, args.model, api_key)
        except Exception as e:
            print(f"[WARN] Gemini generation failed, falling back to template: {e}", file=sys.stderr)
    else:
        print('[INFO] GEMINI_API_KEY not set. Using template output.', file=sys.stderr)

    if not content:
        content = build_marp_template(title, synopsis)

    # Embed SVG placeholders as images
    content_with_images = embed_placeholders_and_images(content, args.out)

    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(content_with_images)
    print(f'Wrote Marp Markdown: {args.out}')


if __name__ == '__main__':
    main()
