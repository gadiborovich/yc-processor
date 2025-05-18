from src.storage.models import DatabaseManager, CompanyUrlRecord

db = DatabaseManager()
session = db.get_session()

try:
    # Get all URLs and their scraping status
    urls = session.query(CompanyUrlRecord).all()
    
    print(f"\nTotal URLs collected: {len(urls)}\n")
    print("Status breakdown:")
    status_counts = {}
    for url in urls:
        status_counts[url.scrape_status] = status_counts.get(url.scrape_status, 0) + 1
    for status, count in status_counts.items():
        print(f"{status}: {count}")
    
    print("\nFirst 10 URLs with their status:")
    for url in urls[:10]:
        print(f"\nURL: {url.url}")
        print(f"Status: {url.scrape_status}")
        print(f"Batch: {url.batch}")
        print(f"Last scraped: {url.last_scraped}")
finally:
    session.close() 