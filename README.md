# YC Company Scraper and Analyzer

A Python-based tool for scraping, analyzing, and classifying YC companies from any batch. The tool automatically categorizes companies into core AI themes and maintains a structured database of company information.

## Features

- Scrapes company data from Y Combinator's company directory
- Extracts detailed information including:
  - Company name and description
  - Location
  - Company website
  - LinkedIn profiles (company and founders)
  - YC batch information
- Uses AI to analyze and classify companies into core themes:
  - AI Agents
  - Industry Transformation
  - AI Infrastructure
- Syncs data to Notion database for easy viewing and analysis
- Exports data to CSV format

## Prerequisites

- Python 3.9+
- Notion API Key (for Notion integration)
- OpenAI API Key (for AI analysis)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/gadiborovich/yc-processor.git
cd yc-processor
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your API keys:
```
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
OPENAI_API_KEY=your_openai_api_key
CLASSIFIER_PROMPT=your_classifier_prompt
```

## Usage

1. Run the main script:
```bash
python src/main.py
```

Additional flags:
- `--batch`: Specify YC batch (e.g., "W25" or "S25")
- `--sync-notion`: Sync data to Notion
- `--export`: Export data to CSV
- `--export-file`: Specify custom export filename

2. Export to CSV:
```bash
python src/main.py --export
```

3. Sync to Notion:
```bash
python src/main.py --sync-notion
```

## Project Structure

```
├── src/
│   ├── analyzer/        # AI analysis and classification
│   │   ├── __init__.py
│   │   └── llm_analyzer.py
│   ├── config/         # Configuration management
│   │   ├── __init__.py
│   │   ├── config.yaml
│   │   └── config_manager.py
│   ├── exporter/       # CSV export functionality
│   │   ├── __init__.py
│   │   └── csv_exporter.py
│   ├── notion/         # Notion integration
│   │   ├── __init__.py
│   │   └── notion_sync.py
│   ├── scraper/        # Web scraping functionality
│   │   ├── __init__.py
│   │   ├── company_details.py
│   │   ├── company_scraper.py
│   │   └── url_discovery.py
│   ├── storage/        # Database models and management
│   │   ├── __init__.py
│   │   └── models.py
│   └── main.py         # Main entry point
├── .gitignore         # Git ignore rules
├── LICENSE           # MIT License
├── README.md         # This documentation
└── requirements.txt  # Python dependencies
```

## Notion Database Setup

1. Create a new Notion database with the following properties:
- Name (title)
- Description (text)
- Core Themes (select)
- Tags (multi-select)
- Website (url)
- Deck (files)
- Company LinkedIn (url)
- Founder LinkedIn (text)
- Location (text)
- Analysis Rationale (text)

2. Share the database with your Notion integration
3. Copy the database ID and add it to your .env file

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Please respect Y Combinator's terms of service and rate limiting when using this tool.
