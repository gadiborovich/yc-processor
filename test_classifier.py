from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager, CompanyData, CompanyUrlRecord
from src.analyzer.llm_analyzer import LLMAnalyzer

# Initialize managers
config = ConfigManager()
db = DatabaseManager()

# Create analyzer
analyzer = LLMAnalyzer(config, db)

# List of companies to analyze
COMPANIES = [
    'https://www.ycombinator.com/companies/cohesive',
    'https://www.ycombinator.com/companies/docket',
    'https://www.ycombinator.com/companies/sava-robotics',
    'https://www.ycombinator.com/companies/godela',
    'https://www.ycombinator.com/companies/bitpatrol'
]

# Get company data from database
session = db.get_session()
companies_to_analyze = []

try:
    for url in COMPANIES:
        company = session.query(CompanyData).join(CompanyUrlRecord).filter(
            CompanyUrlRecord.url == url
        ).first()
        
        if company:
            print(f"\nCompany: {company.name}")
            print(f"Description: {company.description}")
            print(f"Location: {company.location}")
            print(f"Website: {company.company_website}")
            print("\nLaunch Post Content:")
            print("-" * 80)
            print(company.company_launches)
            print("-" * 80)
            
            companies_to_analyze.append({
                "id": company.id,
                "name": company.name,
                "company_launches": company.company_launches
            })
finally:
    session.close()

if companies_to_analyze:
    print(f"\nAnalyzing {len(companies_to_analyze)} companies...")
    analyzer.analyze_companies(companies_to_analyze)

# Print results
print("\nClassification Results:")
print("=" * 80)

session = db.get_session()
try:
    for url in COMPANIES:
        company = session.query(CompanyData).join(CompanyUrlRecord).filter(
            CompanyUrlRecord.url == url
        ).first()
        
        if company:
            print(f"\nCompany: {company.name}")
            print(f"Description: {company.description}")
            print(f"Core Theme: {company.ai_core_theme}")
            print(f"Tags: {company.get_ai_tags_list()}")
            print(f"Rationale: {company.ai_rationale}")
            print("-" * 80)
finally:
    session.close() 