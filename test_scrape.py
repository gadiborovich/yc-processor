from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager
from src.scraper.company_scraper import CompanyScraper
from playwright.sync_api import sync_playwright

# Initialize managers
config = ConfigManager()
db = DatabaseManager()

# Create scraper
scraper = CompanyScraper(config, db)

# Test URLs that were previously failing
urls = [
    'https://www.ycombinator.com/companies/cohesive',
    'https://www.ycombinator.com/companies/docket',
    'https://www.ycombinator.com/companies/sava-robotics',
    'https://www.ycombinator.com/companies/godela',
    'https://www.ycombinator.com/companies/bitpatrol'
]

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    
    for url in urls:
        print(f"\nTesting scrape of: {url}")
        result = scraper.scrape_company(browser, url)
        
        if result:
            print("\nScraped Data:")
            for key, value in result.items():
                if key == 'company_launches':
                    print(f"\nCompany Launches Content Preview (first 1000 chars):")
                    print("-" * 80)
                    print(value[:1000])
                    print("-" * 80)
                    print(f"Total length of company_launches: {len(value)} characters")
                else:
                    print(f"{key}: {value}")
            print("=" * 80)
    
    browser.close() 