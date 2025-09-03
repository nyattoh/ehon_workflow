# 絵本作成ワークフロープロジェクト

GitHub Actions で `stories/*.txt` をもとに絵本風の HTML スライドを生成し、GitHub Pages に自動公開します。

### 必要な設定
- **GitHub Pages の設定（必須）**: リポジトリの Settings → Pages → Build and deployment を「GitHub Actions」に設定。
- **リポジトリのシークレット（AI 生成を使う場合に必要）**: `GEMINI_API_KEY` を追加。
  - 手順: Settings → Secrets and variables → Actions → New repository secret
  - Name: `GEMINI_API_KEY`
  - Value: Google AI Studio で発行した API キー
  - 未設定でも動作しますが、その場合はテンプレート文章で生成されます（AI 生成なし）。

### 使い方（最短）
1. **このリポジトリをフォーク**して自分のアカウントに取り込みます。
2. （任意/推奨）上記の **`GEMINI_API_KEY` をシークレットに設定** します。
3. **`stories/sample.txt` を編集**して題名とあらすじを書き込み、コミット＆プッシュします。

   推奨フォーマットの例:
   ```
   題名: ねこのぼうけん
   あらすじ: 町に住む子ねこが、小さな冒険に出かけます。出会いと発見を通じて、ネコらしさを発揮します。
   ```

4. プッシュ後、Actions のワークフロー（`.github/workflows/storybook.yml`）が自動実行され、`dist/index.html` を生成して **GitHub Pages にデプロイ**します（1〜2分程度）。
5. 公開 URL は、リポジトリの「Deployments」→ `github-pages`、または Settings → Pages の「Visit site」から確認できます。

### 仕組み（ざっくり）
- 変更がプッシュされた `stories/**/*.txt` をトリガーにワークフローが起動。
- `scripts/generate_html_story.py` がテキストを読み込み、（`GEMINI_API_KEY` があれば Gemini で）スライド用テキストを生成し、`dist/index.html` を出力。
- Actions が `dist` を GitHub Pages に公開。

### ローカルで試す（任意）
```bash
pip install google-generativeai
# PowerShell の例（Windows）
$env:GEMINI_API_KEY = "<あなたのAPIキー>"  # AI 生成を使う場合
python scripts/generate_html_story.py --input stories/sample.txt --out dist/index.html
```
`dist/index.html` をブラウザで開くとプレビューできます。

### よくある質問 / トラブルシュート
- **ページが表示されない**: Settings → Pages で Build and deployment が「GitHub Actions」になっているか、Actions が成功しているかを確認してください。
- **AI で生成されない**: `GEMINI_API_KEY` をリポジトリシークレットに設定してください（未設定時はテンプレート出力）。
- **文字化け**: テキストファイルは UTF-8 で保存してください。