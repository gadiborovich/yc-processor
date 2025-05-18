from src.storage.models import DatabaseManager, CompanyData, CompanyUrlRecord

db = DatabaseManager()
session = db.get_session()

try:
    # Get Cohesive's data
    company = session.query(CompanyData).join(CompanyUrlRecord).filter(
        CompanyUrlRecord.url == 'https://www.ycombinator.com/companies/cohesive'
    ).first()
    
    if company:
        print("\nCohesive Company Data:")
        print(f"Name: {company.name}")
        print(f"Location: {company.location}")
        print(f"Description: {company.description}")
        print(f"YC Website: {company.yc_website}")
        print(f"Company Website: {company.company_website}")
        print(f"Founder Names: {company.founder_names}")
        print(f"Company LinkedIn URLs: {company.company_linkedin_urls}")
        print(f"Founder LinkedIn URLs: {company.founder_linkedin_urls}")
        print(f"YC Batch: {company.yc_batch}")
        print("\nCompany Launches Text:")
        print(company.company_launches)
    else:
        print("Company data not found")
finally:
    session.close() 