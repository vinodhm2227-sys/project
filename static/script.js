/* ==========================================================
   script.js
   Handles all frontend behavior:
     - Sending the URL to /scrape
     - Showing loading/status states
     - Sending chat questions to /chat
     - Rendering chat bubbles

   HOW THE FRONTEND COMMUNICATES WITH FLASK:
   We use the browser's built-in `fetch()` function to send HTTP
   requests to our Flask routes (/scrape and /chat). We send data as
   JSON in the request body, and Flask sends back a JSON response
   which we read with `response.json()`. This is the same pattern
   almost every modern web app uses to talk to its backend without
   reloading the page.
   ========================================================== */

// Grab references to all the DOM elements we'll need.
const urlInput = document.getElementById("url-input");
const scrapeBtn = document.getElementById("scrape-btn");
const loadingIndicator = document.getElementById("loading-indicator");
const statusBox = document.getElementById("status-box");

const chatSection = document.getElementById("chat-section");
const chatWindow = document.getElementById("chat-window");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const clearChatBtn = document.getElementById("clear-chat-btn");

/**
 * Shows a status message under the URL input.
 * type: "success" or "error" -- controls the styling.
 */
function showStatus(message, type) {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
  statusBox.classList.remove("hidden");
}

/**
 * Adds a chat bubble to the chat window and scrolls to the bottom.
 * sender: "user" or "bot"
 */
function addChatMessage(text, sender) {
  const bubble = document.createElement("div");
  bubble.className = `chat-message ${sender}`;
  bubble.textContent = text;
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return bubble;
}

/**
 * Shows a temporary "Bot is typing..." bubble and returns it so we
 * can remove/replace it once the real answer arrives.
 */
function showTypingIndicator() {
  const bubble = document.createElement("div");
  bubble.className = "chat-message bot typing";
  bubble.textContent = "Bot is typing...";
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return bubble;
}

/* ---------------------------------------------------------
   SCRAPE BUTTON
   --------------------------------------------------------- */
scrapeBtn.addEventListener("click", scrapeWebsite);
urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") scrapeWebsite();
});

async function scrapeWebsite() {
  const url = urlInput.value.trim();

  if (!url) {
    showStatus("Please enter a website URL.", "error");
    return;
  }

  // Reset UI state before starting.
  statusBox.classList.add("hidden");
  loadingIndicator.classList.remove("hidden");
  scrapeBtn.disabled = true;
  chatSection.classList.add("hidden");

  try {
    const response = await fetch("/scrape", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const data = await response.json();

    if (data.success) {
      showStatus(`✅ ${data.message} (${data.characters_scraped} characters extracted)`, "success");

      // Reveal the chat section and greet the user.
      chatSection.classList.remove("hidden");
      chatWindow.innerHTML = "";
      addChatMessage("You can now ask questions about this website.", "bot");
    } else {
      showStatus(`❌ ${data.error}`, "error");
    }
  } catch (err) {
    showStatus(`❌ Network error: ${err.message}`, "error");
  } finally {
    loadingIndicator.classList.add("hidden");
    scrapeBtn.disabled = false;
  }
}

/* ---------------------------------------------------------
   CHAT SEND BUTTON
   --------------------------------------------------------- */
sendBtn.addEventListener("click", sendQuestion);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendQuestion();
});

async function sendQuestion() {
  const question = chatInput.value.trim();
  if (!question) return;

  addChatMessage(question, "user");
  chatInput.value = "";
  sendBtn.disabled = true;

  const typingBubble = showTypingIndicator();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const data = await response.json();
    typingBubble.remove();

    if (data.success) {
      addChatMessage(data.answer, "bot");
    } else {
      addChatMessage(`⚠️ ${data.error}`, "bot");
    }
  } catch (err) {
    typingBubble.remove();
    addChatMessage(`⚠️ Network error: ${err.message}`, "bot");
  } finally {
    sendBtn.disabled = false;
  }
}

/* ---------------------------------------------------------
   CLEAR CHAT BUTTON
   --------------------------------------------------------- */
clearChatBtn.addEventListener("click", () => {
  chatWindow.innerHTML = "";
  addChatMessage("Chat cleared. Ask a new question about this website.", "bot");
});
