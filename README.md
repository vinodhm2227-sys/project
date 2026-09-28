# Web-Scraping Chatbot

A simple, beginner-friendly Python + Flask web app that lets you enter a
website URL, scrapes the readable text from that page, and then lets
you chat with an AI about that content.

---

## 1. Project Overview

You paste in a website URL. The app downloads the page, strips out all
the "noise" (scripts, styles, navigation bars, footers), and keeps
just the readable text. That text is stored temporarily in the
server's memory. You can then ask questions in a chat window, and an
LLM (OpenAI's API) answers using **only** that scraped text — if the
answer isn't in there, it tells you so instead of guessing.

This project is intentionally kept small: no database, no React, no
Docker, no LangChain — just Flask, BeautifulSoup, requests, and plain
HTML/CSS/JS, so it's easy to read every line and understand exactly
what's happening.

---

## 2. Features

- Clean, responsive web UI (HTML/CSS/JS, no frameworks)
- URL input with validation and a "Scrape Website" button
- Loading indicator + status messages during scraping
- Removes scripts, styles, nav, footer, forms, etc. before extracting text
- In-memory storage of scraped content (no database needed)
- Chat interface for asking questions about the scraped site
- Chatbot answers strictly from scraped content, with a clear
  "not found" message when the answer isn't there
- "Clear Chat" button
- Friendly error handling for bad URLs, timeouts, blocked pages, etc.
- Basic security: URL validation, request timeouts, text-length caps,
  blocking of internal/private network addresses, and `robots.txt`
  respect

---

## 3. Technologies Used

| Layer     | Technology                          |
|-----------|--------------------------------------|
| Backend   | Python, Flask                        |
| Scraping  | requests, BeautifulSoup4             |
| AI        | OpenAI API (`gpt-4o-mini`)           |
| Frontend  | HTML, CSS, JavaScript (vanilla)      |
| Config    | python-dotenv (`.env` file)          |

---

## 4. Project Structure

```text
web_scraping_chatbot/
│
├── app.py              # Flask app & routes (/, /scrape, /chat)
├── scraper.py           # Downloads & cleans website text
├── chatbot.py            # Sends question + scraped text to the LLM
├── requirements.txt
├── .env                 # Your API key goes here (not committed to git)
├── .gitignore
│
├── templates/
│   └── index.html        # Main page
│
└── static/
    ├── style.css         # Styling
    └── script.js          # Frontend logic (fetch calls to Flask)
```

---

## 5. Installation (Windows + VS Code)

### Step 1 — Install Python

Make sure Python 3.9+ is installed. Check in a terminal:

```powershell
python --version
```

If not installed, get it from https://www.python.org/downloads/ and
make sure to check **"Add Python to PATH"** during installation.

### Step 2 — Open the project in VS Code

Open VS Code → File → Open Folder → select the `web_scraping_chatbot`
folder.

---

## 6. Virtual Environment Setup

Using a virtual environment keeps this project's packages separate
from other Python projects on your machine.

Open the VS Code terminal (`` Ctrl+` ``) and run:

```powershell
python -m venv venv
```

Activate it (Windows PowerShell):

```powershell
venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run this once first:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Or, using Command Prompt (cmd.exe) instead of PowerShell:

```cmd
venv\Scripts\activate.bat
```

You'll know it worked when you see `(venv)` at the start of your
terminal prompt.

---

## 7. Installing Requirements

With the virtual environment activated:

```powershell
pip install -r requirements.txt
```

This installs Flask, requests, beautifulsoup4, python-dotenv, and
openai.

---

## 8. Setting the API Key

1. Open the `.env` file in the project folder.
2. Replace the placeholder with your real OpenAI API key:

```text
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

3. Save the file. **Never** share this file or commit it to GitHub —
   it's already listed in `.gitignore` to help prevent that.

You can get an API key from https://platform.openai.com/api-keys

---

## 9. Running the Flask Application

With the virtual environment still activated:

```powershell
python app.py
```

You should see output like:

```text
 * Running on http://127.0.0.1:5000
```

Open that address (`http://127.0.0.1:5000`) in your web browser.

### Alternative: running from Jupyter

Flask apps don't run well *inside* a Jupyter notebook cell (they block
the kernel), but you can still use Jupyter's terminal panel:

1. Open Jupyter → New → Terminal.
2. `cd` into the project folder.
3. Activate the virtual environment and run `python app.py` exactly as
   above.

---

## 10. Example Usage

1. Open the app in your browser.
2. Enter a URL, e.g. `https://example.com`, and click **Scrape
   Website**.
3. Wait for the "Website scraped successfully" status message.
4. In the chat box that appears, type a question, e.g.:
   - "What is this website about?"
   - "What services are provided?"
5. Press **Send** (or Enter) and read the bot's answer.
6. Click **Clear Chat** at any time to reset the conversation (the
   scraped content stays available).

---

## 11. Common Errors

| Error message                                                   | Cause / Fix                                                            |
|-------------------------------------------------------------------|--------------------------------------------------------------------------|
| "Please enter a valid URL starting with http:// or https://"      | The URL is missing a scheme. Add `https://` to the front.               |
| "Could not connect to that website."                              | The site is down, or the URL/domain is wrong.                           |
| "The website took too long to respond."                           | Slow or unresponsive server — try again later.                          |
| "The website returned an error (HTTP ###)."                       | The site returned a non-200 status (404, 403, 500, etc.).               |
| "This website's robots.txt does not allow automated scraping..."  | The site explicitly disallows bots for that page.                       |
| "No readable text could be found on that page."                   | Page is empty, image-only, or entirely JavaScript-rendered.             |
| "No website has been scraped yet."                                | You tried to chat before scraping a site.                               |
| "No OpenAI API key was found."                                    | `.env` is missing `OPENAI_API_KEY` or wasn't saved correctly.           |
| "The AI service returned an error."                               | Invalid/expired API key, no credits, or OpenAI service issue.           |

---

## 12. Future Improvements

- Support scraping multiple pages of a site (not just one URL)
- Add conversation memory so follow-up questions have context
- Persist scraped content to a database for multiple concurrent users
- Add authentication so each user has their own scraped session
- Support JavaScript-rendered pages (e.g. using Playwright/Selenium)
- Add citations showing which part of the page an answer came from
- Swap in a different/local LLM provider

---

## 13. How Everything Works (Full Flow)

```text
User enters URL
       ↓
Flask receives URL           (app.py -> /scrape route)
       ↓
Requests downloads webpage    (scraper.py -> requests.get)
       ↓
BeautifulSoup extracts text   (scraper.py -> BeautifulSoup parsing)
       ↓
Text is stored                (app.py -> scraped_data dict, in memory)
       ↓
User asks question
       ↓
Chatbot receives question + scraped content   (app.py -> /chat route)
       ↓
LLM generates answer          (chatbot.py -> OpenAI API call)
       ↓
Answer displayed in browser   (script.js -> renders chat bubble)
```

### A closer look at each piece

- **`requests`**: Sends an HTTP GET request to the target URL, just
  like a browser does, and returns the raw HTML plus a status code.
- **BeautifulSoup**: Parses that raw HTML into a navigable tree, lets
  us delete unwanted tags (`script`, `style`, `nav`, `footer`, ...),
  and then extracts the remaining human-readable text.
- **Flask routes**: `@app.route("/scrape", methods=["POST"])` and
  `@app.route("/chat", methods=["POST"])` are Python functions that
  run whenever the browser sends a request to those URLs. They read
  JSON input, do the work, and return JSON output.
- **Frontend → Flask**: `script.js` uses `fetch()` to POST JSON to
  `/scrape` and `/chat`, then reads the JSON response to update the
  page — no full page reloads needed.
- **Chatbot → LLM**: `chatbot.py` builds a prompt containing strict
  instructions, the scraped website text, and the user's question,
  then sends it to OpenAI's chat completion endpoint and returns the
  model's reply.

Happy building! 🎉
