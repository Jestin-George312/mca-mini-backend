import google.generativeai as genai
import json
import os

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-pro-latest")


def generate_questions_with_gemini(topic_title, pdf_text, num_questions=5):
    """
    Generate MCQs using Gemini model based on topic title and PDF text.
    Returns a list of JSON objects (questions with options).
    """
    prompt = f"""
    You are a quiz generator AI.

    Generate {num_questions} multiple choice questions (A–D)
    strictly about the topic "{topic_title}" using the following study material.

    Study Material:
    {pdf_text[:12000]}

    Rules:
    - Each question must have exactly 4 options labeled A, B, C, D.
    - Provide one correct option only.
    - Avoid repetition.
    - Return output as pure JSON — no extra text or markdown.

    Example output:
    [
      {{
        "question_text": "What is the capital of France?",
        "option_a": "Paris",
        "option_b": "Berlin",
        "option_c": "Madrid",
        "option_d": "Rome",
        "correct_option": "A"
      }}
    ]
    """

    try:
        response = model.generate_content(prompt)
        text_output = response.text.strip()
        # Attempt to load JSON
        questions = json.loads(text_output)
        return questions
    except json.JSONDecodeError:
        print("[ERROR] Gemini returned invalid JSON")
        return None
    except Exception as e:
        print(f"[ERROR] Gemini request failed: {e}")
        return None
