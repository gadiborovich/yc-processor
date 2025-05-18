#!/usr/bin/env python3
import os
import logging
import argparse
from tqdm import tqdm
from typing import List

from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager
from src.scraper.url_discovery import YCDirectoryScraper
from src.scraper.company_scraper import CompanyScraper
from src.analyzer.llm_analyzer import LLMAnalyzer
from src.exporter.csv_exporter import CSVExporter
from src.notion.notion_sync import NotionSync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("yc_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="YC Company Scraper")
    
    # Configuration file
    parser.add_argument("--config", type=str, default="src/config/config.yaml",
                        help="Path to configuration file")
    
    # Data directory
    parser.add_argument("--data-dir", type=str, default="data",
                        help="Directory for data storage")
    
    # Batch selection
    parser.add_argument("--batches", type=str, nargs="+",
                        help="YC batches to scrape (e.g., W25 S24)")
    
    # Operation flags
    parser.add_argument("--scrape-only", action="store_true",
                        help="Only scrape URLs and company data, don't analyze")
    parser.add_argument("--analyze-only", action="store_true",
                        help="Only analyze existing company data, don't scrape")
    parser.add_argument("--export", action="store_true",
                        help="Export data to CSV")
    parser.add_argument("--sync-notion", action="store_true",
                        help="Sync data to Notion (if configured)")
    
    # Limits
    parser.add_argument("--url-limit", type=int, default=None,
                        help="Maximum number of URLs to scrape")
    parser.add_argument("--company-limit", type=int, default=None,
                        help="Maximum number of companies to analyze")
    
    # Export file
    parser.add_argument("--export-file", type=str, default=None,
                        help="Filename for export (default is auto-generated)")
    
    return parser.parse_args()


def main():
    """Main application entry point."""
    # Parse command line arguments
    args = parse_args()
    
    # Load configuration
    config = ConfigManager(args.config)
    
    # Initialize database
    db_path = os.path.join(args.data_dir, "yc_companies.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = DatabaseManager(db_path)
    
    # Initialize modules
    url_scraper = YCDirectoryScraper(config, db)
    company_scraper = CompanyScraper(config, db)
    llm_analyzer = LLMAnalyzer(config, db)
    exporter = CSVExporter(config, db)
    notion_sync = NotionSync(config, db)
    
    # Get batches to scrape (from args or config)
    batches = args.batches if args.batches else config.get_batches()
    
    # Execute workflow
    if not args.analyze_only:
        # Step 1: Scrape company URLs from YC directory
        for batch in batches:
            logger.info(f"Scraping URLs for batch: {batch}")
            urls = url_scraper.scrape_directory(batch)
            logger.info(f"Found {len(urls)} company URLs for batch {batch}")
        
        # Step 2: Scrape company details
        pending_urls = url_scraper.get_pending_urls(args.url_limit)
        logger.info(f"Scraping details for {len(pending_urls)} companies")
        
        if pending_urls:
            company_scraper.scrape_companies(pending_urls)
    
    if not args.scrape_only:
        # Step 3: Analyze companies with LLM
        companies_to_analyze = company_scraper.get_companies_for_analysis(args.company_limit)
        logger.info(f"Analyzing {len(companies_to_analyze)} companies with LLM")
        
        if companies_to_analyze:
            llm_analyzer.analyze_companies(companies_to_analyze)
    
    # Step 4: Export to CSV (if requested)
    if args.export:
        logger.info("Exporting company data to CSV")
        
        if args.export_file:
            csv_path = exporter.export_all_companies(args.export_file)
        else:
            csv_path = exporter.export_all_companies()
        
        logger.info(f"Exported data to: {csv_path}")
    
    # Step 5: Sync to Notion (if requested and configured)
    if args.sync_notion:
        logger.info("Syncing company data to Notion")
        sync_count = notion_sync.sync_all_companies()
        logger.info(f"Synced {sync_count} companies to Notion")
    
    logger.info("YC Company Scraper workflow completed")


if __name__ == "__main__":
    main() 