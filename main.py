import json
import os
from pathlib import Path
from typing import List, Optional

from anthropic import Anthropic, APIError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="議事録要約ツール")

BASE_DIR = Path(__file__).parent
INDEX_HTML = BASE_DIR / "index.html"

MODEL = "claude-sonnet-4-5"
MAX_INPUT_CHARS = 50_000

SYSTEM_PROMPT = """あなたは優秀な議事録要約アシスタントです。
ユーザーから渡される会議の議事録を読み取り、以下の4項目を日本語で構造化して抽出してください。

1. summary: 会議の概要を簡潔に3行で（配列、各要素が1行）
2. decisions: 会議で決定した事項（配列、各要素が1つの決定事項）
3. todos: ToDo項目。各要素は {"task": タスク内容, "assignee": 担当者またはnull, "due": 期限またはnull} 形式の辞書
4. next_actions: 次のアクション（配列、各要素が1つのアクション）

必ず以下のJSONスキーマに従って、JSONオブジェクトのみを返してください。前後に説明文やコードブロック記号は付けないでください。

{
  "summary": ["...", "...", "..."],
  "decisions": ["...", "..."],
  "todos": [{"task": "...", "assignee": "...またはnull", "due": "...またはnull"}],
  "next_actions": ["...", "..."]
}

該当する情報が議事録内に無い場合は、その項目は空配列([])にしてください。担当者・期限が不明な場合はnullにしてください。"""


class SummarizeRequest(BaseModel):
    minutes: str = Field(..., description="議事録テキスト")


class TodoItem(BaseModel):
    task: str
    assignee: Optional[str] = None
    due: Optional[str] = None


class SummarizeResponse(BaseModel):
    summary: List[str]
    decisions: List[str]
    todos: List[TodoItem]
    next_actions: List[str]


def _get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY が設定されていません。.env ファイルを確認してください。",
        )
    return Anthropic(api_key=api_key)


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("レスポンスからJSONを抽出できませんでした")
    return json.loads(text[start : end + 1])


@app.get("/")
def index():
    return FileResponse(INDEX_HTML)


@app.post("/api/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    minutes = (req.minutes or "").strip()
    if not minutes:
        raise HTTPException(status_code=400, detail="議事録テキストが空です。")
    if len(minutes) > MAX_INPUT_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"議事録が長すぎます（{MAX_INPUT_CHARS}文字以内にしてください）。",
        )

    client = _get_client()

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": minutes}],
        )
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude APIエラー: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"予期しないエラー: {e}") from e

    raw_text = "".join(
        block.text for block in message.content if getattr(block, "type", "") == "text"
    )

    try:
        data = _extract_json(raw_text)
    except (ValueError, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"AIの応答を解析できませんでした: {e}",
        ) from e

    try:
        return SummarizeResponse(
            summary=data.get("summary", []) or [],
            decisions=data.get("decisions", []) or [],
            todos=[TodoItem(**t) for t in (data.get("todos", []) or [])],
            next_actions=data.get("next_actions", []) or [],
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"AIの応答が想定スキーマと一致しません: {e}",
        ) from e
