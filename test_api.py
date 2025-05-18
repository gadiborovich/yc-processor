import os
from dotenv import load_dotenv, dotenv_values
import google.generativeai as genai

def test_gemini_api():
    # Load environment variables
    print("📝 Current working directory:", os.getcwd())
    
    # Print all variables from .env file
    print("\n📋 Contents of .env file:")
    config = dotenv_values(".env")
    for key in config:
        value = config[key]
        print(f"{key}: {value[:4]}..." if value else f"{key}: None")
    
    load_dotenv()
    
    # Configure the Gemini API
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("\n❌ Error: GOOGLE_API_KEY not found in .env file")
        return False
    
    # Debug info about the key (safely)
    print(f"\n🔑 API Key found (first 4 chars): {api_key[:4]}...")
    print(f"🔢 API Key length: {len(api_key)}")
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Try a simple generation with Gemini 2.5 Pro
        print("\n🤖 Testing with gemini-2.5-pro-preview-05-06 model...")
        model = genai.GenerativeModel('gemini-2.5-pro-preview-05-06')
        response = model.generate_content("Analyze this startup pitch: 'We're building an AI-powered personal assistant for software developers.'")
        print("\n✅ Successfully connected to Gemini API!")
        print("\nTest response:", response.text)
        return True
    except Exception as e:
        print(f"\n❌ Error connecting to Gemini API: {str(e)}")
        if "quota" in str(e).lower():
            print("\n💡 Tip: You need to set up billing in Google Cloud Console to use Gemini 2.5 Pro.")
            print("Visit: https://console.cloud.google.com/billing")
        return False

if __name__ == "__main__":
    test_gemini_api() 