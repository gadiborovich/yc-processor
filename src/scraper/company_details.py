import logging
from typing import Dict, Set, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import Page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("company_details")

class CompanyDetailsScraper:
    """
    Scraper for extracting detailed information from YC company pages.
    """
    
    def scrape_company_details(self, page: Page) -> Dict:
        """
        Scrape all relevant details from a company page.
        
        Args:
            page: Playwright page object already navigated to company URL
            
        Returns:
            Dictionary containing all scraped company details
        """
        # Wait for key elements to load
        page.wait_for_selector('h1', timeout=30000)  # Company name
        page.wait_for_selector('div.group.flex.gap-4', timeout=30000)  # Founder info
        page.wait_for_selector('span:has-text("Location:")', timeout=30000)  # Location
        
        # Get page content after elements are loaded
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Initialize result dictionary
        company_details = {
            'name': '',
            'location': '',
            'description': '',
            'company_website': '',
            'company_linkedin_urls': set(),
            'founder_linkedin_urls': set(),
            'founder_names': set(),
            'company_launches': ''
        }
        
        # Extract main section
        main_section = soup.find('section', class_=lambda x: x and 'relative' in x and 'isolate' in x)
        if not main_section:
            return company_details
        
        # Extract company name and description
        name_element = soup.find('h1')
        if name_element:
            company_details['name'] = name_element.text.strip()
            
            # Description is in the next div after h1
            desc_div = name_element.find_next('div')
            if desc_div and not any(x in desc_div.get_text() for x in ['Y Combinator', 'Active', 'Company', 'Jobs']):
                company_details['description'] = desc_div.get_text().strip()
        
        # Extract location
        location_span = soup.find('span', string='Location:')
        if location_span:
            next_span = location_span.find_next('span')
            if next_span:
                company_details['location'] = next_span.text.strip()
        
        # Extract founder information
        founder_divs = soup.find_all('div', class_='group flex gap-4')
        for div in founder_divs:
            text = div.get_text().strip()
            if 'Founder' in text:
                # Get founder name
                name = text.replace('Founder', '').strip()
                company_details['founder_names'].add(name)
                
                # Get founder LinkedIn
                linkedin = div.find('a', href=lambda x: x and 'linkedin.com/in/' in x)
                if linkedin:
                    company_details['founder_linkedin_urls'].add(linkedin['href'])
        
        # Extract company LinkedIn URLs
        company_linkedin_links = soup.find_all('a', href=lambda x: x and 'linkedin.com/company/' in x)
        for link in company_linkedin_links:
            company_details['company_linkedin_urls'].add(link['href'])
        
        # Extract company website (first non-YC, non-social external link)
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if (href.startswith('https://') and 
                not any(x in href for x in ['linkedin.com', 'youtube.com', 'ycombinator.com', 
                                          'startupschool.org', 'twitter.com', 'x.com', 
                                          'facebook.com', 'instagram.com', 'calendly.com'])):
                company_details['company_website'] = href
                break
        
        # Get the full text for company_launches
        company_details['company_launches'] = main_section.get_text(separator=' ', strip=True)
        
        # Convert sets to lists for JSON serialization
        company_details['company_linkedin_urls'] = list(company_details['company_linkedin_urls'])
        company_details['founder_linkedin_urls'] = list(company_details['founder_linkedin_urls'])
        company_details['founder_names'] = list(company_details['founder_names'])
        
        # Log what we found
        logger.info(f"Scraped data for {company_details['name']}:")
        for key, value in company_details.items():
            if key != 'company_launches':
                logger.info(f"{key}: {value}")
        
        return company_details 