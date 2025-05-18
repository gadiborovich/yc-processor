import os
import logging
import csv
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime

from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager, CompanyData, CompanyUrlRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("csv_exporter")


class CSVExporter:
    """
    Exporter for company data to CSV format.
    """
    
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        """
        Initialize the CSV exporter.
        
        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config = config_manager
        self.db = db_manager
        self.export_path = self.config.get('storage.export_path', 'data/exports')
        self.csv_columns = self.config.get_csv_columns()
        
        # Create export directory if it doesn't exist
        os.makedirs(self.export_path, exist_ok=True)
    
    def export_all_companies(self, filename: Optional[str] = None) -> str:
        """
        Export all companies to a CSV file.
        
        Args:
            filename: Optional filename for the CSV file
        
        Returns:
            Path to the exported CSV file
        """
        logger.info("Exporting all companies to CSV")
        
        # Generate default filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yc_companies_{timestamp}.csv"
        
        # Get all companies
        companies = self._get_all_companies()
        
        # Export to CSV
        csv_path = os.path.join(self.export_path, filename)
        
        logger.info(f"Exporting {len(companies)} companies to {csv_path}")
        
        return self._export_to_csv(companies, csv_path)
    
    def export_companies_by_batch(self, batch: str, filename: Optional[str] = None) -> str:
        """
        Export companies from a specific batch to a CSV file.
        
        Args:
            batch: YC batch identifier (e.g., "W25")
            filename: Optional filename for the CSV file
        
        Returns:
            Path to the exported CSV file
        """
        logger.info(f"Exporting companies from batch {batch} to CSV")
        
        # Generate default filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yc_companies_{batch}_{timestamp}.csv"
        
        # Get companies from the specified batch
        companies = self._get_companies_by_batch(batch)
        
        # Export to CSV
        csv_path = os.path.join(self.export_path, filename)
        
        logger.info(f"Exporting {len(companies)} companies from batch {batch} to {csv_path}")
        
        return self._export_to_csv(companies, csv_path)
    
    def export_analyzed_companies(self, filename: Optional[str] = None) -> str:
        """
        Export only companies that have been analyzed to a CSV file.
        
        Args:
            filename: Optional filename for the CSV file
        
        Returns:
            Path to the exported CSV file
        """
        logger.info("Exporting analyzed companies to CSV")
        
        # Generate default filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yc_companies_analyzed_{timestamp}.csv"
        
        # Get analyzed companies
        companies = self._get_analyzed_companies()
        
        # Export to CSV
        csv_path = os.path.join(self.export_path, filename)
        
        logger.info(f"Exporting {len(companies)} analyzed companies to {csv_path}")
        
        return self._export_to_csv(companies, csv_path)
    
    def _get_all_companies(self) -> List[Dict]:
        """
        Get all companies from the database.
        
        Returns:
            List of company data dictionaries
        """
        session = self.db.get_session()
        
        try:
            companies = []
            
            company_records = session.query(CompanyData).all()
            
            for record in company_records:
                company_data = self._format_company_data(record)
                companies.append(company_data)
            
            return companies
        
        finally:
            session.close()
    
    def _get_companies_by_batch(self, batch: str) -> List[Dict]:
        """
        Get companies from a specific batch from the database.
        
        Args:
            batch: YC batch identifier (e.g., "W25")
        
        Returns:
            List of company data dictionaries
        """
        session = self.db.get_session()
        
        try:
            companies = []
            
            company_records = session.query(CompanyData).filter_by(yc_batch=batch).all()
            
            for record in company_records:
                company_data = self._format_company_data(record)
                companies.append(company_data)
            
            return companies
        
        finally:
            session.close()
    
    def _get_analyzed_companies(self) -> List[Dict]:
        """
        Get companies that have been analyzed from the database.
        
        Returns:
            List of company data dictionaries
        """
        session = self.db.get_session()
        
        try:
            companies = []
            
            company_records = session.query(CompanyData).filter(
                CompanyData.ai_core_theme.isnot(None)
            ).all()
            
            for record in company_records:
                company_data = self._format_company_data(record)
                companies.append(company_data)
            
            return companies
        
        finally:
            session.close()
    
    def _format_company_data(self, record: CompanyData) -> Dict:
        """
        Format a company data record for CSV export.
        
        Args:
            record: CompanyData record
        
        Returns:
            Dictionary with formatted company data
        """
        company_data = {
            "name": record.name,
            "location": record.location,
            "description": record.description,
            "yc_website": record.yc_website,
            "company_website": record.company_website,
            "company_linkedin_urls": ",".join(record.get_company_linkedin_url_list()),
            "founder_linkedin_urls": ",".join(record.get_founder_linkedin_url_list()),
            "company_launches": record.company_launches,
            "founder_names": ",".join(record.get_founder_names_list()),
            "ai_core_theme": record.ai_core_theme,
            "ai_tags": ",".join(record.get_ai_tags_list()),
            "ai_rationale": record.ai_rationale,
            "yc_batch": record.yc_batch
        }
        
        return company_data
    
    def _export_to_csv(self, companies: List[Dict], csv_path: str) -> str:
        """
        Export company data to a CSV file.
        
        Args:
            companies: List of company data dictionaries
            csv_path: Path to the CSV file
        
        Returns:
            Path to the exported CSV file
        """
        try:
            # Filter the dictionary columns to only include the configured columns
            filtered_companies = []
            for company in companies:
                filtered_company = {col: company.get(col, "") for col in self.csv_columns}
                filtered_companies.append(filtered_company)
            
            # Convert to DataFrame and export
            df = pd.DataFrame(filtered_companies)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # Export to CSV
            df.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
            
            logger.info(f"Successfully exported {len(companies)} companies to {csv_path}")
            
            return csv_path
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise 