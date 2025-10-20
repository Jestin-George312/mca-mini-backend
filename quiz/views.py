from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.conf import settings

from topic_analysis.models import Topic
from .models import QuizQuestion
from .utils.pdf_utils import extract_text_from_pdf
import google.generativeai as genai
import json, os

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-pro-latest')


class GenerateQuestionsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, topic_id):
        try:
            topic = Topic.objects.get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Assuming your Topic model has a download_url to PDF
        pdf_url = topic.material.download_url if hasattr(topic, 'material') else None
        if not pdf_url:
            return Response({'error': 'PDF URL not found for this topic'}, status=status.HTTP_404_NOT_FOUND)

        # Download PDF content
        try:
            import requests
            response = requests.get(pdf_url)
            response.raise_for_status()
            pdf_bytes = response.content
        except Exception as e:
            return Response({'error': f'Failed to download PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Extract PDF text
        pdf_text = extract_text_from_pdf(pdf_bytes)
        topic_title = topic.topic_name

        # Create prompt for Gemini
        prompt = f"""
You are a quiz generator.

Generate 5 multiple choice questions (A–D) about the topic "{topic_title}".
Use the following study material for context.

{pdf_text[:12000]}

Return the output strictly as JSON in this format:
[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_option": "A"
  }}
]
"""

        # Generate questions using Gemini
        try:
            response = model.generate_content(prompt)
            output_text = response.text.strip()

            # Remove ```json and ``` markers
            if output_text.startswith("```json"):
                output_text = output_text[len("```json"):].strip()
            if output_text.startswith("```"):
                output_text = output_text[3:].strip()
            if output_text.endswith("```"):
                output_text = output_text[:-3].strip()

            # Parse JSON
            questions = json.loads(output_text)
        except json.JSONDecodeError:
            return Response({
                "error": "Gemini returned invalid JSON",
                "raw_output": output_text
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Failed to generate questions: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save questions to DB
        for q in questions:
            QuizQuestion.objects.create(
                topic=topic,
                question_text=q.get("question_text"),
                option_a=q.get("option_a"),
                option_b=q.get("option_b"),
                option_c=q.get("option_c"),
                option_d=q.get("option_d"),
                correct_option=q.get("correct_option"),
            )

        return Response({
            "topic": topic_title,
            "questions_created": len(questions),
            "questions": questions
        })
