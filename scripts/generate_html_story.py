#!/usr/bin/env python3
"""
Generate HTML slides from story input using Gemini API.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


def generate_html_slides(title: str, slides: list) -> str:
    """Generate HTML slides from slide content."""
    
    # Create slide HTML
    slide_html = ""
    for i, slide_content in enumerate(slides, 1):
        slide_content = slide_content.strip()
        if not slide_content:
            continue
            
        # Convert markdown-like formatting to HTML
        slide_content = slide_content.replace('\n', '<br>')
        
        slide_html += f'''
    <div class="slide" id="slide-{i}">
        <div class="slide-content">
            {slide_content}
        </div>
    </div>'''
    
    # Complete HTML template
    html_template = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            overflow: hidden;
        }}
        
        .slideshow-container {{
            position: relative;
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .slide {{
            display: none;
            width: 90%;
            max-width: 800px;
            height: 80%;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 60px;
            text-align: center;
            position: relative;
            animation: slideIn 0.5s ease-in-out;
        }}
        
        .slide.active {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        
        .slide-content {{
            font-size: 2.5em;
            line-height: 1.6;
            color: #333;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .slide-content h1 {{
            font-size: 3em;
            color: #667eea;
            margin-bottom: 30px;
            text-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        
        .slide-content h2 {{
            font-size: 2.8em;
            color: #764ba2;
            margin-bottom: 20px;
        }}
        
        .slide-content p {{
            margin-bottom: 20px;
        }}
        
        .navigation {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 20px;
            z-index: 1000;
        }}
        
        .nav-btn {{
            background: rgba(255,255,255,0.9);
            border: none;
            border-radius: 50px;
            padding: 15px 25px;
            font-size: 1.2em;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        .nav-btn:hover {{
            background: white;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }}
        
        .nav-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .slide-counter {{
            position: fixed;
            top: 30px;
            right: 30px;
            background: rgba(255,255,255,0.9);
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateX(50px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        @media (max-width: 768px) {{
            .slide {{
                width: 95%;
                height: 85%;
                padding: 40px 30px;
            }}
            
            .slide-content {{
                font-size: 2em;
            }}
            
            .slide-content h1 {{
                font-size: 2.5em;
            }}
            
            .slide-content h2 {{
                font-size: 2.2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="slideshow-container">
        {slide_html}
    </div>
    
    <div class="slide-counter">
        <span id="current-slide">1</span> / <span id="total-slides">{len(slides)}</span>
    </div>
    
    <div class="navigation">
        <button class="nav-btn" id="prev-btn" onclick="changeSlide(-1)">← 前へ</button>
        <button class="nav-btn" id="next-btn" onclick="changeSlide(1)">次へ →</button>
    </div>
    
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        
        function showSlide(n) {{
            slides[currentSlide].classList.remove('active');
            currentSlide = (n + totalSlides) % totalSlides;
            slides[currentSlide].classList.add('active');
            
            document.getElementById('current-slide').textContent = currentSlide + 1;
            document.getElementById('prev-btn').disabled = currentSlide === 0;
            document.getElementById('next-btn').disabled = currentSlide === totalSlides - 1;
        }}
        
        function changeSlide(direction) {{
            showSlide(currentSlide + direction);
        }}
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowLeft') {{
                changeSlide(-1);
            }} else if (e.key === 'ArrowRight') {{
                changeSlide(1);
            }}
        }});
        
        // Initialize
        showSlide(0);
        
        // Auto-advance slides (optional)
        // setInterval(() => {{
        //     if (currentSlide < totalSlides - 1) {{
        //         changeSlide(1);
        //     }}
        // }}, 5000);
    </script>
</body>
</html>'''
    
    return html_template


def build_html_slides_from_gemini(title: str, synopsis: str, api_key: str, model_name: str = "gemini-1.5-flash") -> str:
    """
    Use Google Gemini to generate story content and create HTML slides.
    If the library or API fails, raise and let caller fallback.
    """
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    
    system_preamble = (
        "You are a children picture-book writer and editor. "
        "Generate concise Japanese text suitable for picture-book slides. "
        "Keep sentences short and friendly."
    )
    # Pass system instruction at model creation (Gemini does not accept a "system" role in messages)
    model = genai.GenerativeModel(model_name, system_instruction=system_preamble)
    user_prompt = f'''次の題名とあらすじから、絵本のストーリーを生成してください。

【重要】以下の形式で出力してください：
- スライド1: タイトルだけ大きく
- スライド2〜8: 1枚に2〜5行、やさしい短文で
- 最後のスライド: おわり と ひとこと（前向きな締め）
- 各スライドの内容を「---」で区切って出力してください
- 重要: コードブロック（```markdown）で囲まず、生のテキストのみを出力してください

題名: {title}
あらすじ:
{synopsis}
'''
    # Send only the user prompt; roles array with "system" is not supported
    res = model.generate_content(user_prompt)
    text = getattr(res, 'text', None) or (res.candidates[0].content.parts[0].text if getattr(res, 'candidates', None) else None)
    if not text:
        raise RuntimeError('Empty response from Gemini')
    
    # Debug: Print raw Gemini output
    print(f'[DEBUG] Raw Gemini output length: {len(text)} characters', file=sys.stderr)
    print(f'[DEBUG] Raw Gemini output (first 500 chars): {text[:500]}', file=sys.stderr)
    print(f'[DEBUG] Raw Gemini output (last 200 chars): {text[-200:]}', file=sys.stderr)
    
    # Remove code block markers if present
    if text.startswith('```markdown'):
        text = text[11:]  # Remove ```markdown
    if text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    
    # Parse the content and create HTML slides
    slides = text.strip().split('---')
    slides = [slide.strip() for slide in slides if slide.strip()]
    
    print(f'[DEBUG] Parsed {len(slides)} slides from Gemini output', file=sys.stderr)
    
    # Generate HTML slides
    html_content = generate_html_slides(title, slides)
    return html_content


def build_html_template(title: str, synopsis: str) -> str:
    """Build a simple HTML template when Gemini API is not available."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    slides = [
        f"# {title}",
        f"# はじまり\n\n{synopsis}",
        "# つづき\n\n- 1つめの出来事\n- 2つめの出来事\n- 3つめの出来事",
        "# おわりに\n\n読んでくれてありがとう！\n({now})"
    ]
    
    return generate_html_slides(title, slides)


def main():
    parser = argparse.ArgumentParser(description='Generate HTML slides from story input')
    parser.add_argument('--input', required=True, help='Input story file')
    parser.add_argument('--out', required=True, help='Output HTML file')
    parser.add_argument('--api-key', help='Gemini API key (optional)')
    
    args = parser.parse_args()
    
    # Read input file
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read().strip()
    except FileNotFoundError:
        print(f'Error: Input file {args.input} not found', file=sys.stderr)
        sys.exit(1)
    
    # Parse title and synopsis
    lines = content.split('\n')
    title = lines[0].replace('題名:', '').strip() if lines[0].startswith('題名:') else 'サンプルストーリー'
    synopsis = '\n'.join(lines[1:]).replace('あらすじ:', '').strip() if len(lines) > 1 else content
    
    print(f'[INFO] Title: {title}', file=sys.stderr)
    print(f'[INFO] Synopsis: {synopsis[:100]}...', file=sys.stderr)
    
    # Generate HTML slides
    api_key = args.api_key or os.environ.get('GEMINI_API_KEY')
    
    if api_key:
        try:
            print('[INFO] Using Gemini API with model: gemini-1.5-flash', file=sys.stderr)
            html_content = build_html_slides_from_gemini(title, synopsis, api_key)
            print('[INFO] Gemini generation successful', file=sys.stderr)
        except Exception as e:
            print(f'[WARN] Gemini generation failed, falling back to template: {e}', file=sys.stderr)
            html_content = build_html_template(title, synopsis)
    else:
        print('[INFO] No API key provided, using template', file=sys.stderr)
        html_content = build_html_template(title, synopsis)
    
    # Write output file
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f'Wrote HTML slides: {args.out}', file=sys.stderr)


if __name__ == '__main__':
    import os
    main()