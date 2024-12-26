// frontend/script.js
async function sendPrompt() {
    const chatContainer = document.getElementById("chat-container");
    const userInputField = document.getElementById("userPrompt");
    const userText = userInputField.value.trim();
  
    if (!userText) return; // don't send empty messages
  
    // Add user's message to chat
    const userMsgDiv = document.createElement("div");
    userMsgDiv.classList.add("message", "user-msg");
    userMsgDiv.textContent = "User: " + userText;
    chatContainer.appendChild(userMsgDiv);
  
    // Clear the input
    userInputField.value = "";
  
    // Show a "Loading..." or some placeholder
    const botMsgDiv = document.createElement("div");
    botMsgDiv.classList.add("message", "bot-msg");
    botMsgDiv.textContent = "Bot: [Thinking...]";
    chatContainer.appendChild(botMsgDiv);
  
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
  
    try {
      // Call the /generate endpoint
      const res = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: userText }),
      });
      const data = await res.json();
  
      // Update bot's message
      botMsgDiv.textContent = "Bot: " + (data.response || "(No response)");
    } catch (err) {
      console.error(err);
      botMsgDiv.textContent = "Bot: [Error receiving response]";
    }
  
    // Scroll to bottom again
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
  