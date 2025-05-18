import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup

from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager, CompanyUrlRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("url_discovery")


class YCDirectoryScraper:
    """
    Scraper for the YC company directory to discover company URLs.
    """
    
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        """
        Initialize the YC directory scraper.
        
        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config = config_manager
        self.db = db_manager
        self.directory_url = self.config.get('scraper.directory_url')
        self.page_load_delay = self.config.get('scraper.page_load_delay', 2)
        self.scroll_delay = self.config.get('scraper.scroll_delay', 1)
        self.timeout = self.config.get('scraper.timeout', 30000)
        self.selectors = self.config.get_selectors()
    
    def scrape_directory(self, batch: str) -> List[str]:
        """
        Scrape the YC directory for company URLs matching the specified batch.
        
        Args:
            batch: YC batch identifier (e.g., "Spring 2025")
        
        Returns:
            List of discovered company URLs
        """
        logger.info(f"Starting to scrape YC directory for batch: {batch}")
        
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True  # Use headless mode for production
            )
            
            try:
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                
                # Navigate to the directory page with batch filter
                encoded_batch = batch.replace(" ", "%20")
                url = f"{self.directory_url}/?batch={encoded_batch}"
                
                # Navigate and wait for initial load
                page.goto(url)
                
                # Wait for any company card to appear (they all have this class)
                company_card_selector = "a._company_i9oky_355"
                page.wait_for_selector(company_card_selector, timeout=30000)
                
                # Function to get current company count
                def get_company_count():
                    return len(page.query_selector_all(company_card_selector))
                
                # Scroll until we reach the bottom
                last_count = 0
                no_change_count = 0
                max_no_change = 3  # Stop after 3 attempts with no new companies
                
                while no_change_count < max_no_change:
                    # Get current count
                    current_count = get_company_count()
                    logger.info(f"Current company count: {current_count}")
                    
                    # Scroll to bottom
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    
                    # Wait a bit for new content
                    page.wait_for_timeout(1500)  # 1.5 seconds should be enough
                    
                    if current_count == last_count:
                        no_change_count += 1
                    else:
                        no_change_count = 0  # Reset if we found new companies
                        logger.info(f"Found {current_count - last_count} new companies")
                    
                    last_count = current_count
                
                # Now get all company URLs
                company_elements = page.query_selector_all(company_card_selector)
                company_urls = []
                
                for element in company_elements:
                    href = element.get_attribute("href")
                    if href and href.startswith("/companies/"):
                        full_url = f"https://www.ycombinator.com{href}"
                        company_urls.append(full_url)
                
                logger.info(f"Found {len(company_urls)} total companies")
                
                # Store URLs in database
                self._store_company_urls(company_urls, batch)
                
                return company_urls
            
            finally:
                browser.close()
    
    def _scroll_to_load_all(self, page: Page) -> None:
        """
        Scroll down the page to load all company cards.
        
        Args:
            page: Browser page
        """
        logger.info("Scrolling to load all companies...")
        
        # Initial count
        last_count = 0
        no_change_count = 0
        max_no_change = 3  # Stop after 3 attempts with no new companies
        
        while no_change_count < max_no_change:
            # Get current count before scrolling
            current_count = page.evaluate(f"document.querySelectorAll('{self.selectors.get('company_card')}').length")
            
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Wait for potential new content to load
            page.wait_for_timeout(1000)  # 1 second
            
            if current_count == last_count:
                no_change_count += 1
            else:
                no_change_count = 0  # Reset if we found new companies
                
            last_count = current_count
            logger.info(f"Current company count: {current_count}")
        
        logger.info(f"Finished scrolling, found {last_count} companies")
    
    def _extract_company_urls(self, page: Page) -> List[str]:
        """
        Extract company URLs from the directory page.
        
        Args:
            page: Browser page
        
        Returns:
            List of company URLs
        """
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        company_cards = soup.select(self.selectors.get('company_card', '.CompanyCard_root__wYiT9'))
        company_urls = []
        
        for card in company_cards:
            link_element = card.select_one(self.selectors.get('company_link', 'a[href]'))
            
            if link_element and "href" in link_element.attrs:
                href = link_element["href"]
                
                # Make sure we have a full URL
                if href.startswith("/"):
                    company_url = f"https://www.ycombinator.com{href}"
                else:
                    company_url = href
                
                company_urls.append(company_url)
        
        return company_urls
    
    def _store_company_urls(self, urls: List[str], batch: str) -> None:
        """
        Store discovered company URLs in the database.
        
        Args:
            urls: List of company URLs
            batch: YC batch identifier
        """
        session = self.db.get_session()
        
        try:
            for url in urls:
                # Check if URL already exists in database
                existing_url = session.query(CompanyUrlRecord).filter_by(url=url).first()
                
                if existing_url:
                    logger.info(f"URL already exists in database: {url}")
                else:
                    # Create new record
                    new_url_record = CompanyUrlRecord(
                        url=url,
                        batch=batch,
                        discovery_date=datetime.utcnow(),
                        scrape_status="pending"
                    )
                    session.add(new_url_record)
                    logger.info(f"Added new URL to database: {url}")
            
            session.commit()
            logger.info(f"Successfully stored {len(urls)} URLs for batch {batch}")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing URLs in database: {e}")
        
        finally:
            session.close()
    
    def get_pending_urls(self, limit: Optional[int] = None) -> List[str]:
        """
        Get URLs that are pending scraping.
        
        Args:
            limit: Maximum number of URLs to return (None for all)
        
        Returns:
            List of pending URLs
        """
        session = self.db.get_session()
        
        try:
            query = session.query(CompanyUrlRecord).filter_by(scrape_status="pending")
            
            if limit is not None:
                query = query.limit(limit)
            
            records = query.all()
            
            return [record.url for record in records]
        
        finally:
            session.close() 