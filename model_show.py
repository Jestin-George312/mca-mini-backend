import google.generativeai as genai
import os
from dotenv import load_dotenv

def list_available_models():
    """
    Connects to the Google Gemini API and lists all available models
    that support the 'generateContent' method.
    """
    try:
        # Load environment variables from the .env file in your project root
        load_dotenv()

        # Get the API key from your environment variables
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            print("Error: GEMINI_API_KEY could not be found in your .env file.")
            print("Please ensure your .env file is in the same directory as this script.")
            return

        genai.configure(api_key=api_key)

        print("--- Checking for available models ---")
        print("The following models support the 'generateContent' method for your API key:")
        
        found_models = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
                found_models = True
        
        if not found_models:
            print("\nNo models supporting 'generateContent' were found for your key.")
            print("This might be an issue with the API key permissions or the project setup in Google AI Studio.")

    except Exception as e:
        print(f"\nAn error occurred while trying to connect to the API: {e}")
        print("Please double-check that your API key is correct and has been enabled.")

if __name__ == "__main__":
    list_available_models()
