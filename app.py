"""
app.py
------
This is the main Flask application file. It ties everything together:

- It defines the web routes (URLs) that the browser can talk to.
- It calls scraper.py to download and clean website text.
- It calls chatbot.py to answer questions using that text.
- It keeps the scraped text in memory (a simple Python variable) so we
  don't need a database for this beginner project.

HOW FLASK ROUTES WORK (quick explanation):
Flask lets us write normal Python functions and "attach" them to a URL
using a decorator like @app.route("/scrape", methods=["POST"]).
When the browser (or JavaScript fetch()) sends a request to that URL,
Flask runs the matching function and sends back whatever that function
returns (here, we return JSON).
"""

import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from scraper import scrape_website, ScraperError
from chatbot import answer_question, ChatbotError

# Load variables from the .env file (like OPENAI_API_KEY) into the
# environment so Python's os.environ can see them. This keeps secrets
# out of our source code.
load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------------------
# IN-MEMORY STORAGE
# ---------------------------------------------------------------------
# For a simple beginner project we don't need a database. We just keep
# the most recently scraped website's text in a Python dictionary that
# lives in server memory. This means:
#   - The data disappears when the Flask server restarts.
#   - Only one "session" of scraped content is remembered at a time.
# This is fine for learning purposes, but in a real production app you
# would use a database or per-user session storage instead.
# ---------------------------------------------------------------------
scraped_data = {
    "url": None,
    "text": None,
}

# Maximum number of characters we keep from a scraped page. This stops
# a huge webpage from using too much memory or blowing past the LLM's
# context/token limits.
MAX_TEXT_LENGTH = 15000


@app.route("/")
def home():
    """
    GET /
    Renders the main HTML page (templates/index.html). This is the
    only "full page load" route in the app -- everything else is
    called quietly in the background by JavaScript using fetch().
    """
    return render_template("index.html")


@app.route("/scrape", methods=["POST"])
def scrape():
    """
    POST /scrape
    Expects JSON: {"url": "https://example.com"}

    Steps:
      1. Read the URL from the incoming JSON request.
      2. Ask scraper.py to download and clean the page text.
      3. Save the result in our in-memory `scraped_data` dict.
      4. Return a JSON response telling the frontend whether it worked.
    """
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"success": False, "error": "Please enter a website URL."}), 400

    try:
        text = scrape_website(url, max_length=MAX_TEXT_LENGTH)
    except ScraperError as e:
        # ScraperError is a custom exception we raise ourselves in
        # scraper.py whenever something goes wrong (bad URL, timeout,
        # blocked by robots.txt, empty page, etc.). Its message is
        # already written to be user-friendly.
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        # Catch-all safety net for anything unexpected.
        return jsonify({"success": False, "error": f"Unexpected error while scraping: {e}"}), 500

    # Save the scraped text so /chat can use it later.
    scraped_data["url"] = url
    scraped_data["text"] = text

    return jsonify({
        "success": True,
        "message": "Website scraped successfully.",
        "url": url,
        "characters_scraped": len(text),
    })


@app.route("/chat", methods=["POST"])
def chat():
    """
    POST /chat
    Expects JSON: {"question": "What is this website about?"}

    Steps:
      1. Make sure a website has already been scraped.
      2. Read the user's question from the JSON request.
      3. Pass the question + the scraped text to chatbot.py.
      4. Return the LLM's answer as JSON.
    """
    if not scraped_data.get("text"):
        return jsonify({
            "success": False,
            "error": "No website has been scraped yet. Please scrape a website first."
        }), 400

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"success": False, "error": "Please enter a question."}), 400

    try:
        answer = answer_question(question, scraped_data["text"])
    except ChatbotError as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error while answering: {e}"}), 500

    return jsonify({"success": True, "answer": answer})


if __name__ == "__main__":
    # debug=True auto-reloads the server when you edit code, and shows
    # helpful error pages in the browser. Turn this off in production.
    app.run(debug=True)
