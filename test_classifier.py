#!/usr/bin/env python3
import os
from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager, CompanyData
from src.analyzer.llm_analyzer import LLMAnalyzer

def main():
    # Initialize managers
    config = ConfigManager()
    db = DatabaseManager('data/yc_companies.db')
    analyzer = LLMAnalyzer(config, db)
    
    # Get a company that has been classified before
    session = db.get_session()
    company = session.query(CompanyData).filter(
        CompanyData.ai_core_theme.isnot(None)
    ).first()
    
    if not company:
        print("No classified companies found in database")
        return
    
    # Print original classification
    print("\nOriginal Classification:")
    print(f"Company: {company.name}")
    print(f"Core Theme: {company.ai_core_theme}")
    print(f"Tags: {company.ai_tags}")
    print(f"Rationale: {company.ai_rationale}")
    
    # Clear classification
    company.ai_core_theme = None
    company.ai_tags = None
    company.ai_rationale = None
    session.commit()
    
    # Reclassify
    print("\nReclassifying company...")
    analyzer.analyze_companies([{
        "id": company.id,
        "name": company.name,
        "company_launches": company.company_launches
    }])
    
    # Refresh company data
    session.refresh(company)
    
    # Print new classification
    print("\nNew Classification:")
    print(f"Company: {company.name}")
    print(f"Core Theme: {company.ai_core_theme}")
    print(f"Tags: {company.ai_tags}")
    print(f"Rationale: {company.ai_rationale}")

if __name__ == "__main__":
    main() 