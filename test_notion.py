import os
from dotenv import load_dotenv
from notion_client import Client
from datetime import datetime

def test_notion_connection():
    # Load environment variables
    load_dotenv()
    
    # Get Notion credentials
    NOTION_API_KEY = os.getenv('NOTION_API_KEY')
    NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
    
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        print("Error: Missing Notion credentials in .env file")
        return False
    
    try:
        # Initialize Notion client
        notion = Client(auth=NOTION_API_KEY)
        
        # First, verify database access
        try:
            database = notion.databases.retrieve(database_id=NOTION_DATABASE_ID)
            print("\nSuccessfully connected to Notion database:")
            print(f"Database Title: {database['title'][0]['plain_text']}")
            print(f"Database ID: {database['id']}")
            print("\nAvailable properties:")
            for prop_name, prop_data in database['properties'].items():
                print(f"- {prop_name} ({prop_data['type']})")
        except Exception as e:
            print(f"\nError accessing database: {str(e)}")
            print("Please verify that:")
            print("1. The database ID is correct")
            print("2. The Notion integration has been added to the database")
            print("3. The integration has write access to the database")
            return False

        # Companies to add with correct data
        companies = [
            {
                "Name": {"title": [{"text": {"content": "Cohesive"}}]},
                "Description": {"rich_text": [{"text": {"content": "The agentic CRM for blue collar businesses"}}]},
                "Core Themes": {"select": {"name": "AI Agents"}},
                "Tags": {"multi_select": [{"name": tag} for tag in ["Vertical-Specific Agents", "Agentic Workflow", "Agentic Services/BPO", "Construction", "Marketing Automation", "Systems of Record"]]},
                "Website": {"url": "https://getcohesiveai.com"},
                "Deck": {"files": [{"name": "YC Page", "type": "external", "external": {"url": "https://www.ycombinator.com/companies/cohesive"}}]},
                "Company LinkedIn": {"url": "https://www.linkedin.com/company/cohesive-ai"},
                "Founder LinkedIn": {"rich_text": [{"text": {"content": "https://www.linkedin.com/in/kevindzhang/, https://www.linkedin.com/in/nam-nguyen96/"}}]},
                "Location": {"rich_text": [{"text": {"content": "New York"}}]},
                "Analysis Rationale": {"rich_text": [{"text": {"content": "Cohesive utilizes autonomous AI agents to fully automate sales and marketing workflows—tasks traditionally handled by outsourced VAs or marketing agencies—for blue-collar service businesses. By embedding vertical-specific agents that conduct market research, outreach, and follow-ups, the platform showcases end-to-end agentic automation. This focus on self-directed, domain-tuned agents exemplifies the AI Agents theme."}}]}
            },
            {
                "Name": {"title": [{"text": {"content": "Docket"}}]},
                "Description": {"rich_text": [{"text": {"content": "AI agents for QA testing"}}]},
                "Core Themes": {"select": {"name": "AI Agents"}},
                "Tags": {"multi_select": [{"name": tag} for tag in ["Agentic Workflow", "MLOps/Dev Tools", "Horizontal B2B"]]},
                "Website": {"url": "https://docketqa.com"},
                "Deck": {"files": [{"name": "YC Page", "type": "external", "external": {"url": "https://www.ycombinator.com/companies/docket"}}]},
                "Company LinkedIn": {"url": None},
                "Founder LinkedIn": {"rich_text": [{"text": {"content": "https://www.linkedin.com/in/nishant-hooda/, https://www.linkedin.com/in/boris-skurikhin/"}}]},
                "Location": {"rich_text": [{"text": {"content": "San Francisco"}}]},
                "Analysis Rationale": {"rich_text": [{"text": {"content": "Docket's core offering is built around autonomous AI agents that write, run, and maintain end-to-end QA tests—tasks normally done by human QA engineers. This directly aligns with the AI Agents theme, where semi- or fully autonomous agents are the primary differentiator. Their use of multimodal agents to interact like humans and keep tests in sync underscores agent-based automation as central to the product."}}]}
            },
            {
                "Name": {"title": [{"text": {"content": "SAVA Robotics"}}]},
                "Description": {"rich_text": [{"text": {"content": "Robot Operators for Sheet Metal"}}]},
                "Core Themes": {"select": {"name": "Industry Transformation"}},
                "Tags": {"multi_select": [{"name": tag} for tag in ["Manufacturing/Industrial"]]},
                "Website": {"url": "https://www.savarobotics.com"},
                "Deck": {"files": [{"name": "YC Page", "type": "external", "external": {"url": "https://www.ycombinator.com/companies/sava-robotics"}}]},
                "Company LinkedIn": {"url": None},
                "Founder LinkedIn": {"rich_text": [{"text": {"content": "https://www.linkedin.com/in/alessiotoniolo, https://www.linkedin.com/in/vedic-patel-539546238, https://www.linkedin.com/in/jakob-knudsen5"}}]},
                "Location": {"rich_text": [{"text": {"content": "San Francisco"}}]},
                "Analysis Rationale": {"rich_text": [{"text": {"content": "SAVA Robotics leverages AI-driven robotics to automate manual press-brake operations in sheet metal manufacturing. By integrating advanced software and on-site engineering, it addresses inefficiencies in a traditionally slow-moving heavy-industry sector. This innovation exemplifies the Industry Transformation theme by modernizing a legacy manufacturing process through deep automation."}}]}
            },
            {
                "Name": {"title": [{"text": {"content": "Godela"}}]},
                "Description": {"rich_text": [{"text": {"content": "AI Physics Engine"}}]},
                "Core Themes": {"select": {"name": "Industry Transformation"}},
                "Tags": {"multi_select": [{"name": tag} for tag in ["Manufacturing/Industrial", "Aerospace"]]},
                "Website": {"url": "http://godela.ai"},
                "Deck": {"files": [{"name": "YC Page", "type": "external", "external": {"url": "https://www.ycombinator.com/companies/godela"}}]},
                "Company LinkedIn": {"url": None},
                "Founder LinkedIn": {"rich_text": [{"text": {"content": "https://www.linkedin.com/in/abhijit-pranav-pamarty, https://www.linkedin.com/in/cinnamon-sipper"}}]},
                "Location": {"rich_text": [{"text": {"content": "San Francisco"}}]},
                "Analysis Rationale": {"rich_text": [{"text": {"content": "Godela's AI-driven physics engine revolutionizes engineering workflows in manufacturing and aerospace by eliminating the need for slow, traditional simulations and costly physical prototypes. By embedding deep software integrations into heavy‐industry verticals, it accelerates and de‐risks product development. This level of transformation in a historically consultant‐ and capital‐intensive process exemplifies the Industry Transformation theme."}}]}
            },
            {
                "Name": {"title": [{"text": {"content": "BitPatrol"}}]},
                "Description": {"rich_text": [{"text": {"content": "Secret detection that actually works"}}]},
                "Core Themes": {"select": {"name": "AI Infrastructure"}},
                "Tags": {"multi_select": [{"name": tag} for tag in ["Cybersecurity", "Security & Compliance", "MLOps/Dev Tools"]]},
                "Website": {"url": "https://www.bitpatrol.io"},
                "Deck": {"files": [{"name": "YC Page", "type": "external", "external": {"url": "https://www.ycombinator.com/companies/bitpatrol"}}]},
                "Company LinkedIn": {"url": None},
                "Founder LinkedIn": {"rich_text": [{"text": {"content": "https://www.linkedin.com/in/christopher-lambert"}}]},
                "Location": {"rich_text": [{"text": {"content": "New York"}}]},
                "Analysis Rationale": {"rich_text": [{"text": {"content": "BitPatrol delivers essential 'picks-and-shovels' tooling for AI security by automatically detecting secrets and ensuring compliance across codebases and environments. Its focus on monitoring, alerting, and remediating security risks underpins enterprise AI adoption rather than building vertical applications or autonomous agents. By providing a foundational layer that all AI-driven projects rely on for confidentiality and integrity, it clearly falls into the AI Infrastructure category."}}]}
            }
        ]

        # Add each company
        for company in companies:
            try:
                response = notion.pages.create(
                    parent={"database_id": NOTION_DATABASE_ID},
                    properties=company
                )
                print(f"\nSuccessfully added {company['Name']['title'][0]['text']['content']} to Notion!")
                print(f"Page ID: {response['id']}")
            except Exception as e:
                print(f"\nError adding {company['Name']['title'][0]['text']['content']}: {str(e)}")
                continue

        return True
        
    except Exception as e:
        print(f"Error connecting to Notion: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Notion API connection...")
    success = test_notion_connection()
    print(f"\nTest {'completed successfully' if success else 'failed'}") 