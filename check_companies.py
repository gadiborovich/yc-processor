from src.storage.models import DatabaseManager, CompanyData, CompanyUrlRecord

# List of companies we just re-scraped
COMPANIES = [
    'https://www.ycombinator.com/companies/cohesive',
    'https://www.ycombinator.com/companies/docket',
    'https://www.ycombinator.com/companies/sava-robotics',
    'https://www.ycombinator.com/companies/godela',
    'https://www.ycombinator.com/companies/bitpatrol'
]

db = DatabaseManager()
session = db.get_session()

try:
    for url in COMPANIES:
        # Get company data
        company = session.query(CompanyData).join(CompanyUrlRecord).filter(
            CompanyUrlRecord.url == url
        ).first()
        
        if company:
            company_name = url.split('/')[-1].replace('-', ' ').title()
            print(f"\n{'='*50}")
            print(f"{company_name} Data:")
            print(f"{'='*50}")
            print(f"Name: {company.name}")
            print(f"Location: {company.location}")
            print(f"Description: {company.description}")
            print(f"Company Website: {company.company_website}")
            print(f"Founder Names: {company.founder_names}")
            print(f"Company LinkedIn URLs: {company.company_linkedin_urls}")
            print(f"Founder LinkedIn URLs: {company.founder_linkedin_urls}")
            print(f"YC Batch: {company.yc_batch}")
            
            # Extract some info from launches text to compare
            launches = company.company_launches.lower()
            print("\nInformation found in launches text but not in fields:")
            
            # Check location
            if not company.location:
                if "location:" in launches:
                    idx = launches.find("location:") + 9
                    location = launches[idx:launches.find("\n", idx) if "\n" in launches[idx:] else len(launches)].strip()
                    print(f"- Location found in text: {location}")
            
            # Check website
            if not company.company_website and "https://" in launches:
                idx = launches.find("https://")
                website = launches[idx:launches.find(" ", idx) if " " in launches[idx:] else len(launches)].strip()
                if not website.startswith("https://www.linkedin.com"):
                    print(f"- Website found in text: {website}")
            
            # Check founders
            if not company.founder_names and "founder" in launches:
                print("- Found founder mentions in text")
            
        else:
            print(f"\nNo data found for {url}")
            
finally:
    session.close() 