import os
import json
import logging
import time
from typing import Dict, List, Optional, Any
from openai import OpenAI

from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager, CompanyData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_analyzer")


class LLMAnalyzer:
    """
    Analyzer for classifying companies using OpenAI's o4-mini model.
    """
    
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        """
        Initialize the LLM analyzer.
        
        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config = config_manager
        self.db = db_manager
        
        # Load API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        # Get model configuration
        self.model_name = self.config.get('analyzer.model', 'o4-mini-2025-04-16')
        self.classification_prompt = self.config.get_classification_prompt()
    
    def analyze_companies(self, companies: List[Dict], max_retries: int = 3, retry_delay: int = 5) -> None:
        """
        Analyze multiple companies using the LLM.
        
        Args:
            companies: List of company dictionaries (must contain 'id' and 'company_launches')
            max_retries: Maximum number of retries for LLM API calls
            retry_delay: Delay between retries in seconds
        """
        logger.info(f"Starting to analyze {len(companies)} companies")
        
        for company in companies:
            company_id = company["id"]
            company_name = company["name"]
            company_launches = company["company_launches"]
            
            logger.info(f"Analyzing company: {company_name} (ID: {company_id})")
            
            # Skip if no company launches text
            if not company_launches or len(company_launches.strip()) < 10:
                logger.warning(f"Skipping company {company_name}: insufficient launch text")
                continue
            
            # Analyze with retries
            retries = 0
            while retries <= max_retries:
                try:
                    # Get classification from LLM
                    classification = self._classify_company(company_launches)
                    
                    # Store classification in database
                    self._store_classification(company_id, classification)
                    
                    logger.info(f"Successfully analyzed company: {company_name}")
                    break
                
                except Exception as e:
                    retries += 1
                    if retries <= max_retries:
                        logger.warning(f"Error analyzing company {company_name} (Attempt {retries}/{max_retries}): {e}")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Failed to analyze company {company_name} after {max_retries} attempts: {e}")
    
    def _classify_company(self, company_launches: str) -> Dict[str, Any]:
        """
        Classify a company using the LLM.
        
        Args:
            company_launches: Company launch text
        
        Returns:
            Dictionary containing classification results
        """
        # First, let the LLM analyze the company without forcing JSON
        analysis_response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a startup analyst expert at analyzing companies based on Antigravity Capital's investment framework."},
                {"role": "user", "content": self.classification_prompt.replace("{{company_launches}}", company_launches)}
            ]
        )
        
        analysis = analysis_response.choices[0].message.content
        
        # Then ask it to format the analysis as JSON
        json_response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a startup analyst that provides structured JSON responses."},
                {"role": "user", "content": f"""Here is your analysis of the company:

{analysis}

Based on this analysis, provide the classification in JSON format with these exact keys:
- core_theme: The Core Theme (or Non-Core) classification
- core_theme_rationale: A brief rationale for the Core Theme classification (2-4 sentences)
- tags: A list of all relevant tag names from the Tag Library that apply to the startup"""},
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        try:
            # Extract classification from response text
            classification_text = json_response.choices[0].message.content.strip()
            
            # Parse JSON
            classification = json.loads(classification_text)
            
            # Validate classification
            if not isinstance(classification, dict):
                raise ValueError("Classification is not a dictionary")
            
            required_keys = ["core_theme", "tags", "core_theme_rationale"]
            for key in required_keys:
                if key not in classification:
                    raise ValueError(f"Classification missing required key: {key}")
            
            # Map core_theme_rationale to rationale for database storage
            classification["rationale"] = classification.pop("core_theme_rationale")
            
            return classification
        
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Raw response: {json_response.choices[0].message.content}")
            raise ValueError(f"Failed to parse LLM response: {e}")
    
    def _store_classification(self, company_id: int, classification: Dict[str, Any]) -> None:
        """
        Store the classification results in the database.
        
        Args:
            company_id: Company ID
            classification: Classification results
        """
        session = self.db.get_session()
        
        try:
            # Get company data
            company = session.query(CompanyData).filter_by(id=company_id).first()
            
            if not company:
                logger.error(f"Company not found with ID: {company_id}")
                return
            
            # Update classification fields
            company.ai_core_theme = classification.get("core_theme")
            company.set_ai_tags(classification.get("tags", []))
            company.ai_rationale = classification.get("rationale")
            
            session.commit()
            logger.info(f"Stored classification for company: {company.name}")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing classification: {e}")
        
        finally:
            session.close()
    
    def get_pending_companies(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get companies that need to be analyzed.
        
        Args:
            limit: Maximum number of companies to return
        
        Returns:
            List of company dictionaries
        """
        session = self.db.get_session()
        
        try:
            # Query for companies that have been scraped but not analyzed
            query = session.query(CompanyData).filter(
                CompanyData.company_launches.isnot(None),
                CompanyData.ai_core_theme.is_(None)
            )
            
            if limit:
                query = query.limit(limit)
            
            # Convert to dictionaries
            companies = []
            for company in query.all():
                companies.append({
                    "id": company.id,
                    "name": company.name,
                    "company_launches": company.company_launches
                })
            
            return companies
        
        finally:
            session.close() 