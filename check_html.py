from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

def print_element_info(element, depth=0):
    indent = "  " * depth
    classes = element.get('class', [])
    class_str = f" class='{' '.join(classes)}'" if classes else ""
    text = element.get_text(strip=True)
    text_preview = f" text='{text[:50]}...'" if text else ""
    print(f"{indent}<{element.name}{class_str}{text_preview}>")

url = 'https://www.ycombinator.com/companies/cohesive'
print(f"\nAnalyzing HTML structure of: {url}")

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    
    content = page.content()
    soup = BeautifulSoup(content, 'html.parser')
    
    print("\nMain section structure:")
    main_section = soup.find('section', class_=lambda x: x and 'relative' in x and 'isolate' in x)
    if main_section:
        for child in main_section.children:
            if child.name:
                print_element_info(child)
                
    print("\nCompany info div structure:")
    info_div = soup.find('div', class_='ycdc-card-new')
    if info_div:
        for child in info_div.children:
            if child.name:
                print_element_info(child)
    
    print("\nSearching for location text:")
    for element in soup.find_all(string=re.compile('Location:', re.I)):
        parent = element.parent
        print(f"Found in: <{parent.name} class='{' '.join(parent.get('class', []))}'>")
        print(f"Full text: {element}")
    
    browser.close() 