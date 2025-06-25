#  LLM browsing Agent (Prototype)

This project is a **prototype** of an intelligent web-browsing agent that uses a Large Language Model (LLM) to interact with websites via a headless browser. The agent can **read, click, scroll, type**, and more—all based on LLM-generated instructions.

---

##  Status: Prototype

>  This is an early-stage prototype. The codebase is **still under development** and may be unstable or incomplete. Expect bugs, missing features, and experimental logic.

---

##  How It Works

The system uses [Playwright](https://playwright.dev/python/docs/intro) to launch a Chromium browser and simulate user interaction. It communicates with an LLM (e.g., running locally with [Ollama](https://ollama.com/)) to:

1. **Summarize the visible contents** of the current page.
2. **Receive a plan** from the LLM based on a user instruction.
3. **Parse the plan** into executable browser actions.
4. **Execute the actions** (click, type, scroll, etc.) and repeat.

---



# Local-Browsing-LLM
LLM ran locally using ollama for giving up to date answers
