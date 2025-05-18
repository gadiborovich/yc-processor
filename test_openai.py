import os
from dotenv import load_dotenv
from openai import OpenAI

def test_openai():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('❌ No OpenAI API key found in .env file')
        return
    
    print(f'🔑 API Key found (first 4 chars): {api_key[:4]}...')
    
    try:
        # Initialize client
        client = OpenAI(api_key=api_key)
        
        # Test API with a simple request
        print('\n🤖 Testing GPT-4 Turbo...')
        response = client.chat.completions.create(
            model='gpt-4-turbo-preview',
            messages=[
                {
                    'role': 'user',
                    'content': 'Analyze this startup pitch: "We\'re building an AI-powered personal assistant for software developers."'
                }
            ]
        )
        
        print('\n✅ OpenAI API test successful!')
        print(f'\nResponse: {response.choices[0].message.content}')
    except Exception as e:
        print(f'\n❌ Error: {str(e)}')

if __name__ == '__main__':
    test_openai() 