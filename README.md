# 議事録要約Webアプリ

**日刊AI Day1** の作品です。議事録を貼り付けると、Claude API が要点・決定事項・ToDo・次のアクションを自動で構造化して返してくれるシングルページWebアプリ。

X: https://x.com/nikkan_aitool

## 機能

- 議事録テキストを貼り付けて1クリックで要約
- 出力は4セクションに構造化
  - 📌 会議の概要（3行）
  - ✅ 決定事項
  - 📋 ToDo（担当者・期限つき）
  - 🔜 次のアクション
- 結果を1クリックでクリップボードにコピー
- ローディング表示・エラーハンドリング込み
- スマホ対応のレスポンシブデザイン

## 技術スタック

- フロントエンド: HTML + CSS + Vanilla JavaScript（1ファイル完結）
- バックエンド: Python / FastAPI
- AI: Anthropic Claude API（`claude-sonnet-4-5`）

## ファイル構成

- `main.py` — FastAPI バックエンド
- `index.html` — フロントエンド（CSS/JS同梱）
- `requirements.txt` — 依存パッケージ
- `.env.example` — APIキー設定例

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. APIキーを設定

`.env.example` をコピーして `.env` を作成し、Anthropic の API キーを記入します。

```bash
cp .env.example .env
# .env を開いて ANTHROPIC_API_KEY=... を実際のキーに書き換える
```

APIキーは https://console.anthropic.com/ で取得できます。

### 3. 起動

```bash
uvicorn main:app --reload
```

ブラウザで http://localhost:8000 にアクセス。

## 使い方

1. テキストエリアに議事録を貼り付け
2. 「要約する」ボタンをクリック（または `Cmd/Ctrl + Enter`）
3. 結果が4セクションで表示される
4. 右上の「コピー」でテキスト形式でクリップボードへコピー

## ライセンス

MIT License — 詳細は [LICENSE](./LICENSE) を参照してください。
