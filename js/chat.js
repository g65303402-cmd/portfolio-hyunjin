// AI 챗봇 위젯 로직
// 백엔드(FastAPI + Claude API) 배포 후, 아래 API_BASE 값을 실제 배포 주소로 교체하세요.
// 예: const API_BASE = "https://portfolio-hyunjin-chatbot.onrender.com";
const API_BASE = "https://portfolio-hyunjin.onrender.com";

const chatToggle = document.getElementById("chatToggle");
const chatPanel = document.getElementById("chatPanel");
const chatClose = document.getElementById("chatClose");
const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");

// 백엔드에 보낼 최근 대화 기록 (역할 + 내용)
let history = [];

chatToggle.addEventListener("click", () => {
  const isHidden = chatPanel.hasAttribute("hidden");
  if (isHidden) {
    chatPanel.removeAttribute("hidden");
    chatInput.focus();
  } else {
    chatPanel.setAttribute("hidden", "");
  }
});

chatClose.addEventListener("click", () => {
  chatPanel.setAttribute("hidden", "");
});

/**
 * 채팅 말풍선을 목록에 추가하고 스크롤을 맨 아래로 이동시킨다.
 * @param {string} text - 표시할 메시지 내용
 * @param {"bot"|"user"|"error"} kind - 말풍선 종류
 */
function appendBubble(text, kind) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble chat-bubble-${kind}`;
  bubble.textContent = text;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return bubble;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendBubble(message, "user");
  chatInput.value = "";
  chatInput.disabled = true;

  const loadingBubble = appendBubble("생각 중...", "bot");

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });

    if (!res.ok) {
      throw new Error(`서버 응답 오류 (${res.status})`);
    }

    const data = await res.json();
    loadingBubble.textContent = data.reply;

    // 대화 기록 업데이트 (최근 20개만 유지)
    history.push({ role: "user", content: message });
    history.push({ role: "assistant", content: data.reply });
    history = history.slice(-20);
  } catch (err) {
    loadingBubble.remove();
    appendBubble(
      "죄송해요, 지금은 답변을 가져올 수 없어요. 잠시 후 다시 시도해주세요.",
      "error"
    );
    console.error(err);
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
});
