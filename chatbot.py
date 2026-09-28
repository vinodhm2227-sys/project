"""
chatbot.py
----------
This file is responsible for answering the user's question using ONLY
the text that was scraped from the website.

HOW THE CHATBOT RECEIVES SCRAPED CONTENT:
app.py keeps the scraped text in memory and passes it into
`answer_question(question, website_text)` every time the user asks
something. We don't need any special "memory" system for the website
content -- we just re-send it as part of the prompt each time.

HOW THE LLM GENERATES ANSWERS:
We build a single prompt that contains:
  1. Clear instructions telling the model to answer ONLY using the
     provided website text, and to say a specific phrase if the
     answer isn't in there.
  2. The scraped website text itself.
  3. The user's question.
We send that prompt to the OpenAI API, and the model's job is just to
read the text and answer based on it -- it doesn't browse the web or
know anything beyond what we gave it.
"""

import os
from openai import OpenAI, OpenAIError

# The exact fallback message required when the answer isn't in the
# scraped content. Keeping it as a constant avoids typos/mismatches.
NOT_FOUND_MESSAGE = "I couldn't find that information in the scraped website content."

# Which OpenAI chat model to use. gpt-4o-mini is small, fast, and
# inexpensive -- a good fit for a simple learning project. You can
# swap this for any chat-completion-capable model your API key has
# access to.
MODEL_NAME = "gpt-4o-mini"

SYSTEM_PROMPT = f"""You are a helpful assistant that answers questions using ONLY the
website content provided to you below. Follow these rules strictly:

1. Only use information found in the provided website content to answer.
2. Do not use any outside knowledge, even if you know the answer.
3. If the answer cannot be found in the website content, respond with
   exactly this sentence and nothing else: "{NOT_FOUND_MESSAGE}"
4. Keep answers concise and directly relevant to the question.
"""


class ChatbotError(Exception):
    """
    Custom exception for chatbot/LLM problems (missing API key, API
    request failure, etc.) with a message safe to show to the user.
    """
    pass


def _get_client() -> OpenAI:
    """
    Creates an OpenAI client using the API key from the environment
    (loaded from .env by app.py via python-dotenv). We check for the
    key ourselves first so we can give a clear, friendly error instead
    of a confusing stack trace if it's missing.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ChatbotError(
            "No OpenAI API key was found. Please set OPENAI_API_KEY in your .env file."
        )
    return OpenAI(api_key=api_key)


def answer_question(question: str, website_text: str) -> str:
    """
    Sends the scraped website text + the user's question to the LLM
    and returns the model's answer as a plain string.

    We truncate the website text defensively here too (in addition to
    the truncation already done in scraper.py) just to be extra safe
    about prompt size.
    """
    client = _get_client()

    max_context_chars = 15000
    trimmed_text = website_text[:max_context_chars]

    user_prompt = f"""WEBSITE CONTENT:
\"\"\"
{trimmed_text}
\"\"\"

QUESTION: {question}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,  # low temperature = more focused, less "creative" answers
            max_tokens=500,
        )
    except OpenAIError as e:
        raise ChatbotError(f"The AI service returned an error: {e}")
    except Exception as e:
        raise ChatbotError(f"Unexpected error while contacting the AI service: {e}")

    answer = response.choices[0].message.content.strip()
    return answer if answer else NOT_FOUND_MESSAGE
