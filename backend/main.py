"""포트폴리오 방문자용 Claude 챗봇 API 서버.

프론트엔드(GitHub Pages 정적 사이트)에서 이 서버의 /api/chat 엔드포인트를
호출하면, 김현진의 포트폴리오 내용을 아는 상태로 Claude가 답변합니다.
"""

import os
from typing import Literal

from anthropic import Anthropic, APIError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── 환경 변수 ────────────────────────────────────────────────────────────
# Render 등 배포 환경의 Environment 설정에 반드시 등록해야 합니다.
ANTHROPIC_API_KEY: str | None = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL: str = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

# 쉼표로 구분된 허용 오리진 목록 (예: 배포된 GitHub Pages 주소)
ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.environ.get(
        "ALLOWED_ORIGINS",
        "https://g65303402-cmd.github.io",
    ).split(",")
    if origin.strip()
]

if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY 환경 변수가 설정되어 있지 않습니다.")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

app = FastAPI(title="김현진 포트폴리오 챗봇 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# ── 포트폴리오 컨텍스트 (시스템 프롬프트) ───────────────────────────────
SYSTEM_PROMPT = """\
당신은 김현진의 포트폴리오 웹사이트에 방문한 사람을 응대하는 AI 어시스턴트입니다.
아래 정보를 바탕으로 김현진을 3인칭으로 소개하듯 친절하고 간결하게 답변하세요.
정보에 없는 내용은 추측하지 말고, 모른다고 솔직히 말한 뒤 이메일(kimhyunjin1356@kakao.com)로
문의하도록 안내하세요. 답변은 2~4문장 내외로 간결하게 작성합니다.

[기본 소개]
- 이름: 김현진
- Mercedes-Benz 자동차 영업 컨설턴트에서 AI·SW 개발자로 커리어 전환 중
- K-디지털 트레이닝 AI·SW 개발 과정 수료 예정

[기술 스택]
- AI/LLM: Python, LangChain, OpenAI SDK, Anthropic SDK, RAG, openWakeWord
- Backend: FastAPI, Streamlit, REST API
- Frontend: React, Streamlit, HTML/CSS/JS
- Tools: Git/GitHub, Jupyter, VS Code, Google Colab, Notion

[프로젝트]
1. 자동차 판매 AI 어시스턴트 (개인 프로젝트)
   - Mercedes-Benz 영업 현장 경험을 도메인으로 활용한 AI 세일즈 어시스턴트
   - LangChain, OpenAI/Anthropic API, Streamlit 사용

2. AI 컨베이어 벨트 안전 시스템 (2026 K-디지털 트레이닝 해커톤, 팀 공장수호대)
   - 제스처·음성·위험구역 접근을 동시에 감지하는 트리플 트리거 안전 정지 시스템
   - 김현진은 백엔드 통합(트리플 트리거 정지 API) 담당
   - Python, FastAPI, Computer Vision, 음성 인식 사용

3. 교통봇 — 음성 기반 대중교통 안내 서비스 (팀 프로젝트, 김현진·문서현·김가람, 2026.04.16~04.29)
   - 호출어 + 음성 질문만으로 실시간 버스 도착 정보 안내
   - 김현진은 KWS(호출어 인식) 파인튜닝 담당: openWakeWord를 직접 녹음한 200개 데이터를
     증강해 약 1,000개로 학습, 네거티브 데이터 학습과 연속 4회 감지로 오탐을 줄여
     호출어 인식 정확도 0.97 달성
   - Whisper 기반 STT, 광주광역시 BIS 공공데이터 API, GPT-SoVITS 기반 TTS 사용
   - TTS 응답 시간을 API 서버 상주 방식으로 20초에서 1~3초로 단축

4. Project Junhyuk — 친구같은 감성 상담 보조자 (팀 프로젝트)
   - LGAI EXAONE-3.0-7.8B-Instruct를 QLoRA(r=16, alpha=32)로 파인튜닝
   - 12개 감정 카테고리, 981개 대화 데이터로 학습 (최적 체크포인트 loss 0.3047)
   - ChromaDB + KR-SBERT 임베딩으로 RAG 구축, 유사 대화 예시 3개를 few-shot으로 주입
   - Python, RAG, 프롬프트 엔지니어링, 모델 평가, API 서버 사용

[연락처]
- 이메일: kimhyunjin1356@kakao.com
- 전화: 010-5796-9159
- GitHub: https://github.com/g65303402-cmd
"""


class ChatMessage(BaseModel):
    """대화 기록 한 개의 발화 단위."""

    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=4000)


class ChatRequest(BaseModel):
    """/api/chat 요청 바디."""

    message: str = Field(..., min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    """/api/chat 응답 바디."""

    reply: str


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """배포 상태 확인용 헬스체크 엔드포인트."""
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """방문자 메시지를 받아 Claude 응답을 반환합니다."""
    messages = [{"role": m.role, "content": m.content} for m in request.history]
    messages.append({"role": "user", "content": request.message})

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
    except APIError as exc:
        # Claude API 호출 실패 (키 오류, 요금 한도 초과 등) 시 502로 응답
        raise HTTPException(status_code=502, detail=f"Claude API 오류: {exc}") from exc

    reply_text = "".join(
        block.text for block in response.content if block.type == "text"
    )
    return ChatResponse(reply=reply_text)
