import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from notion_client import Client

from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager, CompanyData, CompanyUrlRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("notion_sync")


class NotionSync:
    """
    Module for synchronizing company data with Notion.
    
    Note: This is a skeleton implementation for future development.
    """
    
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        """
        Initialize the Notion sync module.
        
        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config = config_manager
        self.db = db_manager
        
        # Check for Notion API token
        self.api_token = os.environ.get("NOTION_API_KEY")
        if not self.api_token:
            logger.warning("NOTION_API_KEY environment variable not set. Notion integration will be disabled.")
            self.enabled = False
            return
        
        # Get Notion database ID
        self.database_id = self.config.get("notion.database_id")
        if not self.database_id or self.database_id.startswith("MISSING_ENV_VAR"):
            logger.warning("Notion database ID not configured. Notion integration will be disabled.")
            self.enabled = False
            return
        
        # Initialize Notion client
        try:
            self.client = Client(auth=self.api_token)
            self.enabled = True
            logger.info(f"Notion integration enabled, using database ID: {self.database_id}")
        except Exception as e:
            logger.error(f"Error initializing Notion client: {e}")
            self.enabled = False
    
    def sync_company(self, company_id: int) -> Optional[str]:
        """
        Sync a company to Notion.
        
        Args:
            company_id: ID of the company to sync
        
        Returns:
            Notion page ID if synced successfully, None otherwise
        """
        if not self.enabled:
            logger.warning("Notion integration is not enabled. Cannot sync company.")
            return None
        
        logger.info(f"Syncing company ID {company_id} to Notion")
        
        session = self.db.get_session()
        
        try:
            # Get company data
            company = session.query(CompanyData).filter_by(id=company_id).first()
            
            if not company:
                logger.error(f"Company not found with ID: {company_id}")
                return None
            
            # Check if company has already been synced
            url_record = company.url_record
            
            if url_record and url_record.notion_page_id:
                # Update existing Notion page
                notion_page_id = self._update_notion_page(company, url_record.notion_page_id)
            else:
                # Create new Notion page
                notion_page_id = self._create_notion_page(company)
                
                # Update URL record with Notion page ID
                if notion_page_id and url_record:
                    url_record.notion_page_id = notion_page_id
                    session.commit()
            
            return notion_page_id
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error syncing company {company_id} to Notion: {e}")
            return None
        
        finally:
            session.close()
    
    def sync_all_companies(self) -> int:
        """
        Sync all companies to Notion.
        
        Returns:
            Number of companies synced
        """
        if not self.enabled:
            logger.warning("Notion integration is not enabled. Cannot sync companies.")
            return 0
        
        logger.info("Syncing all companies to Notion")
        
        session = self.db.get_session()
        
        try:
            # Get all companies that have been analyzed
            company_records = session.query(CompanyData).filter(
                CompanyData.ai_core_theme.isnot(None)
            ).all()
            
            sync_count = 0
            
            for company in company_records:
                notion_page_id = self.sync_company(company.id)
                
                if notion_page_id:
                    sync_count += 1
            
            logger.info(f"Successfully synced {sync_count}/{len(company_records)} companies to Notion")
            
            return sync_count
        
        finally:
            session.close()
    
    def _create_notion_page(self, company: CompanyData) -> Optional[str]:
        """
        Create a new page in Notion for the company.
        
        Args:
            company: Company data record
        
        Returns:
            Notion page ID if created successfully, None otherwise
        """
        try:
            # Build the properties object for the new page
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": company.name
                            }
                        }
                    ]
                }
            }
            
            # Add description if it exists
            if company.description:
                properties["Description"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": company.description
                            }
                        }
                    ]
                }
            
            # Add core theme if it exists
            if company.ai_core_theme:
                properties["Core Themes"] = {
                    "select": {
                        "name": company.ai_core_theme
                    }
                }
            
            # Add tags if they exist
            if company.ai_tags:
                properties["Tags"] = {
                    "multi_select": [
                        {"name": tag} for tag in company.get_ai_tags_list()
                    ]
                }
            
            # Add website if it exists
            if company.company_website:
                properties["Website"] = {
                    "url": company.company_website
                }
            
            # Add YC profile link as Deck
            if company.yc_website:
                properties["Deck"] = {
                    "files": [
                        {
                            "name": "YC Page",
                            "type": "external",
                            "external": {
                                "url": company.yc_website
                            }
                        }
                    ]
                }
            
            # Add company LinkedIn if it exists
            company_linkedin = company.get_company_linkedin_url_list()
            if company_linkedin:
                properties["Company LinkedIn"] = {
                    "url": company_linkedin[0] if company_linkedin else None
                }
            
            # Add founder LinkedIn URLs if they exist
            founder_linkedin = company.get_founder_linkedin_url_list()
            if founder_linkedin:
                properties["Founder LinkedIn"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": ", ".join(founder_linkedin)
                            }
                        }
                    ]
                }
            
            # Add location if it exists
            if company.location:
                properties["Location"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": company.location
                            }
                        }
                    ]
                }
            
            # Add analysis rationale if it exists
            if company.ai_rationale:
                properties["Analysis Rationale"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": company.ai_rationale
                            }
                        }
                    ]
                }
            
            # Create the page
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.info(f"Created Notion page for company: {company.name}")
            
            return response["id"]
        
        except Exception as e:
            logger.error(f"Error creating Notion page for company {company.name}: {e}")
            return None
    
    def _update_notion_page(self, company: CompanyData, page_id: str) -> Optional[str]:
        """
        Update an existing page in Notion for the company.
        
        Args:
            company: Company data record
            page_id: Notion page ID
        
        Returns:
            Notion page ID if updated successfully, None otherwise
        """
        try:
            # Build the properties object for the page update
            properties = {}
            
            # Update description if it exists
            if company.description:
                properties["Description"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": company.description
                            }
                        }
                    ]
                }
            
            # Update core theme if it exists
            if company.ai_core_theme:
                properties["Core Themes"] = {
                    "select": {
                        "name": company.ai_core_theme
                    }
                }
            
            # Update tags if they exist
            if company.ai_tags:
                properties["Tags"] = {
                    "multi_select": [
                        {"name": tag} for tag in company.get_ai_tags_list()
                    ]
                }
            
            # Update website if it exists
            if company.company_website:
                properties["Website"] = {
                    "url": company.company_website
                }
            
            # Update YC profile link as Deck
            if company.yc_website:
                properties["Deck"] = {
                    "files": [
                        {
                            "name": "YC Page",
                            "type": "external",
                            "external": {
                                "url": company.yc_website
                            }
                        }
                    ]
                }
            
            # Update company LinkedIn if it exists
            company_linkedin = company.get_company_linkedin_url_list()
            if company_linkedin:
                properties["Company LinkedIn"] = {
                    "url": company_linkedin[0] if company_linkedin else None
                }
            
            # Update founder LinkedIn URLs if they exist
            founder_linkedin = company.get_founder_linkedin_url_list()
            if founder_linkedin:
                properties["Founder LinkedIn"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": ", ".join(founder_linkedin)
                            }
                        }
                    ]
                }
            
            # Update location if it exists
            if company.location:
                properties["Location"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": company.location
                            }
                        }
                    ]
                }
            
            # Update analysis rationale if it exists
            if company.ai_rationale:
                properties["Analysis Rationale"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": company.ai_rationale
                            }
                        }
                    ]
                }
            
            # Update the page
            response = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            logger.info(f"Updated Notion page for company: {company.name}")
            
            return response["id"]
        
        except Exception as e:
            logger.error(f"Error updating Notion page for company {company.name}: {e}")
            return None 