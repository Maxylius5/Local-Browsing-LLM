import re
import time
import json
import requests
from playwright.sync_api import sync_playwright

# ONFIG 
OLLAMA_API = "http://localhost:11434/api/chat"
MODEL = "qwen3:30b-a3b"

#PROMPT TEMPLATE
WEB_AGENT_PROMPT = """
You are a web browsing assistant. You can issue exactly one of the following actions per response:

1. SEARCH[query]  
2. CLICK[text or CSS selector]  
3. READ[CSS selector or 0 for all visible text]  
4. FINAL[final answer]

Respond only with the following two lines, no more and no less:

Thought: <brief reasoning or note>  
Action: ACTION_TYPE[argument]

Rules:  
- Always output exactly one action per response.  
- Use SEARCH[...] to look for information based on the user's query.  
- After SEARCH, use CLICK[...] to open relevant results.  
- After CLICK, use READ[...] to extract text from the page.  
- If CSS selectors fail twice, use READ[0] to read all visible text.  
- If no useful information is found, respond with FINAL[...] politely concluding.  
- Do not repeat the same action indefinitely; try to progress.  
- Keep your "Thought" line very brief and focused; do not write long internal monologues, unless necessery for reasoning.

User query: {query}

"""



def query_ollama(messages):
    response = requests.post(
        OLLAMA_API,
        json={
            "model": MODEL,
            "stream": True,
            "messages": messages
        },
        stream=True
    )

    full_response = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            full_response += data.get("message", {}).get("content", "")
    return full_response



def parse_action(response):
    match = re.search(r'Action:\s*(\w+)\[(.*?)\]', response, re.DOTALL)
    return (match.group(1).upper(), match.group(2).strip()) if match else (None, None)

def run_browser_agent(user_question):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        messages = [
            {"role": "system", "content": "You are a web agent that simulates web browsing to extract information."},
            {"role": "user", "content": WEB_AGENT_PROMPT.format(query=user_question)}
        ]

        while True:
            print("\n💬 Asking LLM...")
            llm_output = query_ollama(messages)
            print("🤖 LLM:\n", llm_output)

            messages.append({"role": "assistant", "content": llm_output})

            action, arg = parse_action(llm_output)

            feedback = ""

            if action == "SEARCH":
                query = arg.replace(" ", "+")
                url = f"https://html.duckduckgo.com/html/?q={query}"
                page.goto(url)
                time.sleep(1)
                all_links = page.locator("a")
                link_texts = all_links.all_text_contents()
                visible_links = [text.strip() for text in link_texts if text.strip()]
                preview = "\n".join(f"{i}. {t[:100]}" for i, t in enumerate(visible_links[:10]))
                feedback = f"Searched DuckDuckGo for '{arg}'.\nFound links:\n{preview}"

            elif action == "CLICK":
                try:

                    if action == "CLICK" and "failed" in feedback:
                        all_links = page.locator("a")
                        link_texts = all_links.all_text_contents()
                        visible_links = [text.strip() for text in link_texts if text.strip()]
                        preview = "\n".join(f"{i}: {t[:80]}" for i, t in enumerate(visible_links[:5]))
                        feedback += f"\nVisible links:\n{preview}"

                    
                    if arg.startswith("css="):
                        selector = arg[len("css="):].strip()
                        page.locator(selector).first.click()
                        feedback = f"Clicked CSS selector: {selector}"
                    elif arg.isdigit():
                        links = page.locator("a")
                        links.nth(int(arg)).click()
                        feedback = f"Clicked link number: {arg}"
                    else:
                        page.click(f"text={arg}")
                        feedback = f"Clicked link with text: {arg}"

                    time.sleep(1)
                
                except Exception as e:
                    all_links = page.locator("a")
                    link_texts = all_links.all_text_contents()
                    visible_links = [text.strip() for text in link_texts if text.strip()]
                    preview = "\n".join(f"{i}. {t[:1000]}" for i, t in enumerate(visible_links[:10]))
                    feedback = f"[⚠️ CLICK failed] Could not click '{arg}': {e}\nAvailable links:\n{preview}"

            elif action == "READ":
                try:
                    if arg == "0":
                        content = page.locator("body").inner_text()
                    elif arg.startswith("css="):

                    
                   
                            selector = arg[len("css="):].strip()
                            content = page.locator(selector).first.inner_text()
                    else:
                            content = page.locator(arg).first.inner_text()
                    feedback = f"Read content:\n{content[:1000]}"
                    print(f"\n📖 READ RESULT (first 500 chars):\n{content[:500]}")
                    
                    titles = page.locator("a").all_text_contents()
                    messages.append({
                        "role": "user",
                        "content": f"Page loaded. Found links:\n" + "\n".join(f"{i}. {t[:80]}" for i, t in enumerate(titles[:5]))
                        })

                except Exception as e:
                    feedback = f"[⚠️ READ failed] {e}"

            
            elif action == "FINAL":
                break

            
            messages.append({"role": "user", "content": feedback})

        browser.close()


user_message=[]
#USAGE
while True:
    user_message=input()
    run_browser_agent(user_message)
