// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
  // Add event listener for Enter key in the input field
  document.getElementById('userPrompt').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      sendPrompt();
    }
  });
});

// Track if a request is in progress
let isRequestInProgress = false;

async function sendPrompt() {
  const chatContainer = document.getElementById("chat-container");
  const userInputField = document.getElementById("userPrompt");
  const sendButton = document.getElementById("sendButton");
  const userText = userInputField.value.trim();

  if (!userText || isRequestInProgress) return; // ignore empty input or if request is in progress

  // Set request flag
  isRequestInProgress = true;
  
  // Disable button and input during processing
  sendButton.disabled = true;
  userInputField.disabled = true;

  // Create a user message in the chat
  const userMsgDiv = document.createElement("div");
  userMsgDiv.classList.add("message", "user-msg");
  
  const userHeader = document.createElement("div");
  userHeader.classList.add("message-header");
  userHeader.textContent = "You";
  
  const userContent = document.createElement("div");
  userContent.classList.add("message-content");
  userContent.textContent = userText;
  
  userMsgDiv.appendChild(userHeader);
  userMsgDiv.appendChild(userContent);
  chatContainer.appendChild(userMsgDiv);

  // Clear the input
  userInputField.value = "";

  // Create bot message with typing indicator
  const botMsgDiv = document.createElement("div");
  botMsgDiv.classList.add("message", "bot-msg");
  
  const botHeader = document.createElement("div");
  botHeader.classList.add("message-header");
  botHeader.textContent = "AI Assistant";
  
  const botContent = document.createElement("div");
  botContent.classList.add("message-content");
  
  // Add typing indicator
  const typingIndicator = document.createElement("div");
  typingIndicator.classList.add("typing-indicator");
  typingIndicator.innerHTML = '<span></span><span></span><span></span>';
  
  botContent.appendChild(typingIndicator);
  botMsgDiv.appendChild(botHeader);
  botMsgDiv.appendChild(botContent);
  chatContainer.appendChild(botMsgDiv);

  // Scroll to bottom
  chatContainer.scrollTop = chatContainer.scrollHeight;

  try {
    // Call your Flask /generate endpoint
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: userText }),
    });
    
    if (!res.ok) {
      throw new Error(`Server responded with status: ${res.status}`);
    }
    
    const data = await res.json();

    // Replace typing indicator with actual response
    botContent.innerHTML = '';
    botContent.textContent = data.response || "I'm sorry, I couldn't generate a response.";
  } catch (err) {
    console.error("Error:", err);
    botContent.innerHTML = '';
    botContent.textContent = "I'm sorry, there was an error processing your request. Please try again later.";
  } finally {
    // Re-enable input and button
    sendButton.disabled = false;
    userInputField.disabled = false;
    userInputField.focus();
    
    // Reset request flag
    isRequestInProgress = false;
    
    // Scroll to bottom again
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
}

// Add a function to check health status
async function checkHealth() {
  try {
    const res = await fetch("/health");
    if (res.ok) {
      const data = await res.json();
      console.log("Health check:", data);
      return true;
    }
    return false;
  } catch (err) {
    console.error("Health check failed:", err);
    return false;
  }
}

// Check health on page load
checkHealth();