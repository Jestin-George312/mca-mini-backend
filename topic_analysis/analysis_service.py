import os
import requests
import pdfplumber
import json
from io import BytesIO
import google.generativeai as genai

from django.conf import settings
from .models import Topic
from materials.models import Material

def call_llm_for_analysis(text_content: str) -> list:
    """
    Calls the Google Gemini API to analyze the text content of a PDF.
    """
    print("--- CALLING GOOGLE GEMINI API ---")
    try:
        # Configure the API key from Django settings
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

        # Use the updated model name: 'gemini-1.5-flash'
        model = genai.GenerativeModel('models/gemini-pro-latest')

        # This is the detailed prompt that instructs the AI
        prompt = f"""
        Analyze the following text content extracted from an educational PDF document.
        Your task is to identify the main topics discussed, evaluate their difficulty,
        and provide a brief summary for each.

        Please return your response as a single, clean JSON array of objects. Do not
        include any introductory text, explanations, or markdown formatting like ```json.
        The JSON array should be the only thing in your response.

        Each object in the array should represent a single topic and must have the
        following structure:
        {{
          "topic_name": "The name of the topic",
          "difficulty_score": A float between 1.0 and 10.0,
          "difficulty_class": A string which is one of "easy", "medium", or "hard",
          "summary": "A concise, 2-3 sentence summary of the topic's content.",
          "sequence_number": An integer representing the order in which the topics appear.
        }}

        Here is the text content to analyze:
        ---
        {text_content}
        ---
        """

        response = model.generate_content(prompt)
        
        # Add detailed logging to see the exact response from the API
        print("--- RAW API Response Text ---")
        print(response.text)
        print("--- End of RAW API Response ---")

        # Clean the response to ensure it's just the JSON part
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        return json.loads(cleaned_text)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from API response: {e}")
        return []
    except Exception as e:
        print(f"An error occurred while calling the Gemini API: {e}")
        return []

def analyze_material(material_id: int):
    """
    The main service function to download, parse, and analyze a material.
    """
    try:
        material = Material.objects.get(pk=material_id)
    except Material.DoesNotExist:
        print(f"Error: Material with ID {material_id} not found.")
        return

    if not material.download_url:
        print(f"Error: Material '{material.title}' has no download URL.")
        return

    print(f"Starting analysis for: {material.title}")

    # Step 1: Download the PDF content
    try:
        response = requests.get(material.download_url)
        response.raise_for_status()
        pdf_content = response.content
        print("PDF downloaded successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF from {material.download_url}: {e}")
        return

    # Step 2: Extract text from the PDF
    full_text = ""
    try:
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        print(f"Text extracted successfully. Total characters: {len(full_text)}")
    except Exception as e:
        print(f"Error extracting text from PDF for material ID {material_id}: {e}")
        return

    if not full_text.strip():
        print("Extracted text is empty. Aborting analysis.")
        return

    # Step 3: Send the text to the LLM for analysis
    topic_data_list = call_llm_for_analysis(full_text)

    if not topic_data_list:
        print("LLM analysis did not return any topics.")
        return

    # Step 4: Clear old analysis results
    Topic.objects.filter(material=material).delete()
    print(f"Cleared old topic entries for '{material.title}'.")

    # Step 5: Create and save new Topic objects
    topics_to_create = []
    for data in topic_data_list:
        if not all(k in data for k in ['topic_name', 'difficulty_score', 'difficulty_class', 'summary', 'sequence_number']):
            print(f"Skipping malformed topic data from LLM: {data}")
            continue
            
        topics_to_create.append(
            Topic(
                material=material,
                topic_name=data['topic_name'],
                difficulty_score=data['difficulty_score'],
                difficulty_class=data['difficulty_class'].lower(),
                summary=data['summary'],
                sequence_number=data['sequence_number']
            )
        )
    
    if topics_to_create:
        Topic.objects.bulk_create(topics_to_create)
        print(f"Successfully saved {len(topics_to_create)} new topics for '{material.title}'.")

    print(f"Analysis complete for: {material.title}")
