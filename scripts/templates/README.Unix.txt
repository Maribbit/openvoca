=================================
  OpenVoca {version}
=================================

QUICK START
-----------
Open a terminal in this folder and run:

    bash run.sh

The app starts a local server and opens in your default browser.
Press Ctrl+C in the terminal to stop the server.

macOS note: The launcher automatically removes the quarantine attribute
  added to downloaded files. No manual Gatekeeper override is needed.

Linux note: If needed, make the script executable first:
  chmod +x run.sh


FIRST-TIME SETUP
----------------
Go to Menu -> Settings -> Model and enter your LLM provider:

  Endpoint  Base URL, with the version prefix your provider uses:
              http://localhost:11434/v1      (Ollama, local)
              https://api.openai.com/v1      (OpenAI)
              https://openrouter.ai/api/v1   (OpenRouter)
              https://api.siliconflow.cn/v1  (SiliconFlow)
              https://api.deepseek.com       (DeepSeek, no version)
            /chat/completions is appended automatically.
  API Key   Your API key (leave blank for local models such as Ollama)
  Model     e.g.  deepseek-chat / gpt-4o-mini / llama3.2

Click "Test Connection" to verify the setup before generating sentences.


HOW TO USE
----------
1. Open the Composer, pick a topic, and click "Generate next sentence".
2. Tap any unfamiliar word to see its definition and hear it pronounced.
3. Mark it "Know" or "Don't Know" to start spaced-repetition review.

OpenVoca resurfaces words you struggle with at growing intervals so they
stick in long-term memory without mindless repetition.


YOUR DATA
---------
All vocabulary and settings are stored in the "data" folder inside this
directory. Back it up to preserve your learning progress across updates.


SUPPORT & UPDATES
-----------------
GitHub:   https://github.com/Maribbit/openvoca
Releases: https://github.com/Maribbit/openvoca/releases
