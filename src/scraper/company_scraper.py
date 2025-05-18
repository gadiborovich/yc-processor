import time
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError
from bs4 import BeautifulSoup

from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager, CompanyUrlRecord, CompanyData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("company_scraper")


class CompanyScraper:
    """
    Scraper for individual YC company pages to extract detailed information.
    """
    
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        """
        Initialize the company scraper.
        
        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config = config_manager
        self.db = db_manager
        self.page_load_delay = self.config.get('scraper.page_load_delay', 2)
        self.max_retries = self.config.get('scraper.max_retries', 3)
        self.timeout = self.config.get('scraper.timeout', 30000)
        self.selectors = self.config.get_selectors()
    
    def scrape_companies(self, urls: List[str]) -> None:
        """
        Scrape detailed information from multiple company pages.
        
        Args:
            urls: List of company URLs to scrape
        """
        logger.info(f"Starting to scrape {len(urls)} company pages")
        
        with sync_playwright() as playwright:
            browser = self._launch_browser(playwright)
            
            try:
                for url in urls:
                    self.scrape_company(browser, url)
            
            finally:
                browser.close()
    
    def scrape_company(self, browser: Browser, url: str, retry_count: int = 0) -> Optional[Dict]:
        """
        Scrape detailed information from a single company page.
        
        Args:
            browser: Browser instance
            url: Company URL to scrape
            retry_count: Current retry attempt
        
        Returns:
            Dictionary of scraped company data or None if scraping failed
        """
        logger.info(f"Scraping company page: {url}")
        
        # Create a new page for each company
        page = self._create_page(browser)
        
        try:
            # Navigate to the company page
            logger.info(f"Navigating to URL: {url}")
            page.goto(url, timeout=self.timeout)
            time.sleep(self.page_load_delay)
            
            # Extract company data from page
            company_data = self._extract_company_data(page, url)
            
            # Store company data in database
            self._store_company_data(company_data, url)
            
            return company_data
        
        except Exception as e:
            logger.error(f"Error scraping company page {url}: {e}")
            
            # Try again if we haven't reached max retries
            if retry_count < self.max_retries:
                logger.info(f"Retrying... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(self.page_load_delay * 2)  # Wait longer before retry
                return self.scrape_company(browser, url, retry_count + 1)
            else:
                # Mark URL as failed in database
                self._mark_url_as_failed(url)
                return None
        
        finally:
            page.close()
    
    def _launch_browser(self, playwright) -> Browser:
        """
        Launch a browser instance with appropriate settings.
        
        Args:
            playwright: Playwright instance
        
        Returns:
            Browser instance
        """
        return playwright.chromium.launch(
            headless=True,
            slow_mo=100,
        )
    
    def _create_page(self, browser: Browser) -> Page:
        """
        Create a new browser page with appropriate settings.
        
        Args:
            browser: Browser instance
        
        Returns:
            Page instance
        """
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        )
        page.set_default_timeout(self.timeout)
        return page
    
    def _extract_company_data(self, page: Page, url: str) -> Dict:
        """
        Extract detailed company information from a company page.
        
        Args:
            page: Browser page
            url: Company URL
        
        Returns:
            Dictionary containing all extracted company information
        """
        # Wait for key elements to load
        page.wait_for_selector('h1', timeout=self.timeout)
        page.wait_for_selector('div.group.flex.gap-4', timeout=self.timeout)
        
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract company name from h1
        name_element = soup.find('h1')
        name = name_element.text.strip() if name_element else "Unknown"
        
        # Extract description from the div with class "prose hidden max-w-full md:block"
        description_element = soup.find('div', class_='prose hidden max-w-full md:block')
        description = None
        if description_element:
            desc_div = description_element.find('div', class_='text-xl')
            if desc_div:
                description = desc_div.text.strip()
        
        # Extract location from the location pill
        location = None
        location_link = soup.find('a', href=lambda x: x and '/companies/location/' in x)
        if location_link:
            location_div = location_link.find('div', class_='yc-tw-Pill')
            if location_div:
                location = location_div.text.strip()
        
        # Extract founder information from the grid
        founder_grid = soup.find('div', class_='grid grid-cols-1 gap-6 sm:grid-cols-2')
        founder_names = []
        founder_linkedin_urls = []
        
        if founder_grid:
            for founder_card in founder_grid.find_all('div', class_='ycdc-card-new'):
                # Get founder name
                name_div = founder_card.find('div', class_='text-xl font-bold')
                if name_div:
                    founder_names.append(name_div.text.strip())
                
                # Get founder LinkedIn
                linkedin_link = founder_card.find('a', href=lambda x: x and 'linkedin.com/in/' in x)
                if linkedin_link:
                    founder_linkedin_urls.append(linkedin_link['href'])
        
        # Extract company LinkedIn URLs
        company_linkedin_links = soup.find_all('a', href=lambda x: x and 'linkedin.com/company/' in x)
        company_linkedin_urls = [link['href'] for link in company_linkedin_links]
        
        # Extract company website (first non-social external link)
        company_website = None
        
        # First try to find website with the link icon
        website_link = soup.find('a', class_=lambda x: x and 'mb-2' in x and 'whitespace-nowrap' in x)
        if website_link:
            href = website_link.get('href')
            if href and href.startswith(('http://', 'https://')):
                company_website = href
        
        # If not found, try other external links
        if not company_website:
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if (href.startswith('https://') and 
                    not any(x in href for x in ['linkedin.com', 'youtube.com', 'ycombinator.com', 
                                              'startupschool.org', 'twitter.com', 'x.com', 
                                              'facebook.com', 'instagram.com', 'calendly.com'])):
                    company_website = href
                    break
        
        # Extract YC batch from the batch pill
        yc_batch = None
        batch_link = soup.find('a', href=lambda x: x and '/companies?batch=' in x)
        if batch_link:
            batch_div = batch_link.find('div', class_='yc-tw-Pill')
            if batch_div:
                # Find the span containing just the batch text
                batch_span = batch_div.find('span')
                if batch_span:
                    yc_batch = batch_span.text.strip()
                else:
                    yc_batch = batch_div.text.strip()
                    # Remove "Y Combinator Logo" if present
                    yc_batch = yc_batch.replace('Y Combinator Logo', '').strip()
        
        # Get the full text for company_launches
        launches_text = []
        
        # First get the main section content
        main_section = soup.find('section', class_=lambda x: x and 'relative' in x and 'isolate' in x)
        if main_section:
            launches_text.append(main_section.get_text(separator=' ', strip=True))
        
        # Then get the detailed launch post content
        launch_card = soup.find('div', class_='ycdc-card-new w-full max-w-[800px] rounded-xl p-8')
        if launch_card:
            # Get the title
            title_div = launch_card.find('div', class_='flex-grow pb-2 text-3xl font-bold')
            if title_div:
                launches_text.append("\nLAUNCH POST:")
                launches_text.append(title_div.get_text(strip=True))
            
            # Get the full launch post content
            article_container = launch_card.find('div', class_='launches-article-container')
            if article_container:
                # Process each paragraph and list
                for element in article_container.find_all(['p', 'ul', 'li', 'strong']):
                    if element.name == 'p':
                        text = ""
                        for content in element.contents:
                            if content.name == 'a':
                                text += f"{content.get_text(strip=True)} ({content.get('href')}) "
                            elif content.name == 'strong':
                                text += f"**{content.get_text(strip=True)}** "
                            elif isinstance(content, str):
                                text += content.strip() + " "
                        launches_text.append(text.strip())
                    elif element.name == 'ul':
                        launches_text.append("")  # Add blank line before list
                    elif element.name == 'li':
                        text = "- "  # Add bullet point
                        for content in element.contents:
                            if content.name == 'a':
                                text += f"{content.get_text(strip=True)} ({content.get('href')}) "
                            elif content.name == 'strong':
                                text += f"**{content.get_text(strip=True)}** "
                            elif isinstance(content, str):
                                text += content.strip() + " "
                        launches_text.append(text.strip())
                    elif element.name == 'strong':
                        launches_text.append(f"**{element.get_text(strip=True)}**")
        
        # Join all text with proper spacing
        final_text = "\n\n".join(filter(None, launches_text))
        
        return {
            "name": name,
            "description": description,
            "location": location,
            "yc_website": url,
            "company_website": company_website,
            "founder_names": founder_names,
            "company_linkedin_urls": company_linkedin_urls,
            "founder_linkedin_urls": founder_linkedin_urls,
            "company_launches": final_text,
            "yc_batch": yc_batch
        }
    
    def _extract_batch_from_url(self, url: str) -> str:
        """
        Extract YC batch identifier from URL or other sources.
        
        Args:
            url: Company URL
        
        Returns:
            YC batch identifier (e.g., "W25") or "Unknown"
        """
        # Try to extract batch from URL (assuming format like /companies/some-company/w25)
        match = re.search(r'([ws]\d{2})(/|$)', url.lower())
        
        if match:
            batch = match.group(1).upper()
            return batch
        
        # If we can't extract batch from URL, try to get it from database
        return self._get_batch_from_database(url)
    
    def _get_batch_from_database(self, url: str) -> str:
        """
        Get YC batch identifier from database.
        
        Args:
            url: Company URL
        
        Returns:
            YC batch identifier or "Unknown"
        """
        session = self.db.get_session()
        
        try:
            url_record = session.query(CompanyUrlRecord).filter_by(url=url).first()
            
            if url_record and url_record.batch:
                return url_record.batch
            
            return "Unknown"
        
        finally:
            session.close()
    
    def _store_company_data(self, data: Dict, url: str) -> None:
        """
        Store the extracted company data in the database.
        
        Args:
            data: Extracted company data
            url: Company URL
        """
        session = self.db.get_session()
        
        try:
            # Get the URL record
            url_record = session.query(CompanyUrlRecord).filter_by(url=url).first()
            
            if not url_record:
                logger.error(f"URL record not found for {url}")
                return
            
            # Check if company data already exists
            existing_data = session.query(CompanyData).filter_by(url_record_id=url_record.id).first()
            
            if existing_data:
                # Update existing record
                existing_data.name = data["name"]
                existing_data.location = data["location"]
                existing_data.description = data["description"]
                existing_data.yc_website = data["yc_website"]
                existing_data.company_website = data["company_website"]
                existing_data.set_founder_names(data["founder_names"])
                existing_data.set_company_linkedin_urls(data["company_linkedin_urls"])
                existing_data.set_founder_linkedin_urls(data["founder_linkedin_urls"])
                existing_data.company_launches = data["company_launches"]
                existing_data.yc_batch = data["yc_batch"]
                existing_data.last_updated = datetime.utcnow()
                
                logger.info(f"Updated existing company data for {data['name']}")
            else:
                # Create new record
                company_data = CompanyData(
                    url_record_id=url_record.id,
                    name=data["name"],
                    location=data["location"],
                    description=data["description"],
                    yc_website=data["yc_website"],
                    company_website=data["company_website"],
                    yc_batch=data["yc_batch"],
                    company_launches=data["company_launches"],
                )
                
                # Set list fields
                company_data.set_founder_names(data["founder_names"])
                company_data.set_company_linkedin_urls(data["company_linkedin_urls"])
                company_data.set_founder_linkedin_urls(data["founder_linkedin_urls"])
                
                session.add(company_data)
                logger.info(f"Added new company data for {data['name']}")
            
            # Update URL record
            url_record.last_scraped = datetime.utcnow()
            url_record.scrape_status = "completed" if data["company_launches"] else "completed_no_launch"
            
            session.commit()
            logger.info(f"Successfully stored company data for {data['name']}")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing company data: {e}")
        
        finally:
            session.close()
    
    def _mark_url_as_failed(self, url: str) -> None:
        """
        Mark a URL as failed in the database.
        
        Args:
            url: Company URL
        """
        session = self.db.get_session()
        
        try:
            url_record = session.query(CompanyUrlRecord).filter_by(url=url).first()
            
            if url_record:
                url_record.last_scraped = datetime.utcnow()
                url_record.scrape_status = "failed"
                session.commit()
                logger.info(f"Marked URL as failed: {url}")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking URL as failed: {e}")
        
        finally:
            session.close()
    
    def get_companies_for_analysis(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get companies that have been scraped but not yet analyzed.
        
        Args:
            limit: Maximum number of companies to return
        
        Returns:
            List of company data dictionaries
        """
        session = self.db.get_session()
        
        try:
            # Get company records that have been scraped successfully but not yet analyzed
            query = session.query(CompanyData).join(
                CompanyUrlRecord
            ).filter(
                CompanyUrlRecord.scrape_status == "completed",
                CompanyData.ai_core_theme.is_(None),
                CompanyData.company_launches.isnot(None)
            )
            
            if limit is not None:
                query = query.limit(limit)
            
            records = query.all()
            
            companies = []
            for record in records:
                companies.append({
                    "id": record.id,
                    "name": record.name,
                    "company_launches": record.company_launches,
                    "yc_batch": record.yc_batch
                })
            
            return companies
        
        finally:
            session.close() 