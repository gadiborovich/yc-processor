import os
from dotenv import load_dotenv
from src.analyzer.llm_analyzer import LLMAnalyzer
from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager

def test_analyzer():
    # Load environment variables
    load_dotenv()
    
    # Print API key info (safely)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('❌ No OpenAI API key found in .env file')
        return
    print(f'🔑 API Key found (first 4 chars): {api_key[:4]}...')
    
    try:
        # Initialize config and DB managers (without actually creating DB)
        config_manager = ConfigManager()
        db_manager = None  # We won't use DB for this test
        
        # Initialize analyzer
        analyzer = LLMAnalyzer(config_manager, db_manager)
        print(f'\n🤖 Using model: {analyzer.model_name}')
        
        # Test company data
        test_company = {
            "id": 1,
            "name": "TestAI Corp",
            "company_launches": """
            We're building an AI-powered code review assistant that helps developers catch bugs, 
            security vulnerabilities, and performance issues before they reach production. 
            Our system uses advanced machine learning to understand code context, suggest improvements, 
            and automatically fix common issues. We integrate directly with GitHub, GitLab, and Bitbucket, 
            making it seamless for development teams to adopt. Early users report 40% faster code reviews 
            and 30% fewer bugs making it to production.
            """
        }
        
        # Test classification
        print('\n📝 Analyzing test company...')
        classification = analyzer._classify_company(test_company["company_launches"])
        
        # Print results
        print('\n✅ Analysis successful!')
        print('\nResults:')
        print(f'Core Theme: {classification["core_theme"]}')
        print(f'Tags: {", ".join(classification["tags"])}')
        print(f'Rationale: {classification["rationale"]}')
        
    except Exception as e:
        print(f'\n❌ Error during test: {str(e)}')

if __name__ == '__main__':
    test_analyzer() 