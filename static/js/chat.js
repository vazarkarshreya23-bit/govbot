/**
 * chat.js — Handles all chatbot interactions
 * Sends user messages to the Flask backend and displays responses.
 */

const chatWindow = document.getElementById("chatWindow");
const userInput  = document.getElementById("userInput");

// ── Send a message ──────────────────────────────────────────────
function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;           // Don't send empty messages
  userInput.value = "";         // Clear the input box

  appendMessage(text, "user"); // Show user's message in chat
  showTyping();                 // Show "bot is typing..." animation

  // Send message to Flask backend
  fetch("/chat", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ message: text })
  })
  .then(response => response.json())   // Parse JSON response
  .then(data => {
    removeTyping();                    // Hide typing indicator
    appendMessage(data.reply, "bot"); // Show bot's reply
  })
  .catch(error => {
    removeTyping();
    appendMessage("⚠️ Something went wrong. Please try again.", "bot");
    console.error("Error:", error);
  });
}

// ── Quick-send from sidebar buttons ────────────────────────────
function sendQuick(text) {
  userInput.value = text;
  sendMessage();
}

// ── Reset the chat session ──────────────────────────────────────
function resetChat() {
  fetch("/reset", {
    method:  "POST",
    headers: { "Content-Type": "application/json" }
  })
  .then(r => r.json())
  .then(data => {
    // Clear all messages from the window
    chatWindow.innerHTML = "";
    appendMessage(data.reply, "bot");
  });
}

// ── Append a message bubble to the chat window ──────────────────
function appendMessage(text, sender) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${sender === "bot" ? "bot-message" : "user-message"}`;

  // Avatar icon
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = sender === "bot" ? "🤖" : "👤";

  // Message bubble
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = text;   // innerHTML allows the HTML tags from bot (bold, etc.)

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chatWindow.appendChild(wrapper);

  // Auto-scroll to bottom
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ── Show animated typing indicator ──────────────────────────────
function showTyping() {
  const typing = document.createElement("div");
  typing.className  = "message bot-message typing";
  typing.id         = "typingIndicator";
  typing.innerHTML  = `
    <div class="avatar">🤖</div>
    <div class="bubble">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    </div>`;
  chatWindow.appendChild(typing);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ── Remove typing indicator ──────────────────────────────────────
function removeTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

// ── Focus input when page loads ──────────────────────────────────
window.addEventListener("load", () => {
  userInput.focus();
});
