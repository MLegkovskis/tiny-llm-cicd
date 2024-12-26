// frontend/script.js
async function sendPrompt() {
    const prompt = document.getElementById("userPrompt").value;
    const responseArea = document.getElementById("responseArea");
  
    responseArea.textContent = "Generating...";
  
    try {
      const res = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      responseArea.textContent = data.response || "(No response)";
    } catch (err) {
      console.error(err);
      responseArea.textContent = "Error calling API.";
    }
  }
  