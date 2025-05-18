from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = 'https://www.ycombinator.com/companies/cohesive'
print(f"\nDebugging scrape of: {url}")

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    content = page.content()
    soup = BeautifulSoup(content, 'html.parser')
    
    print("\nLooking for main content div:")
    main_content = soup.find('div', class_=lambda x: x and 'flex flex-col gap-8' in x)
    if main_content:
        print("Found main content div")
        print("Text content:", main_content.get_text()[:200])
    else:
        print("Main content div not found")
    
    print("\nLooking for company info card:")
    info_card = soup.find('div', class_='ycdc-card-new')
    if info_card:
        print("Found info card")
        print("Text content:", info_card.get_text()[:200])
    else:
        print("Info card not found")
    
    print("\nLooking for location span:")
    location_spans = soup.find_all('span')
    for span in location_spans:
        if span.string and 'Location:' in span.string:
            print("Found location span")
            print("Next sibling:", span.next_sibling)
            break
    
    print("\nLooking for founder divs:")
    founder_divs = soup.find_all('div', class_='group flex gap-4')
    for div in founder_divs:
        print("\nFound founder div:")
        print("Text content:", div.get_text())
        linkedin = div.find('a', href=lambda x: x and 'linkedin.com/in/' in x)
        if linkedin:
            print("LinkedIn URL:", linkedin['href'])
    
    print("\nLooking for company website:")
    links = soup.find_all('a', href=True)
    for link in links:
        href = link['href']
        if href.startswith('https://') and not 'linkedin.com' in href and not 'youtube.com' in href and not 'ycombinator.com' in href:
            print("Found website:", href)
    
    browser.close() 