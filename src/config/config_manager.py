import os
import yaml
from typing import Dict, Any, List
from dotenv import load_dotenv

class ConfigManager:
    """
    Configuration manager to load and provide access to application settings
    from config files and environment variables.
    """
    
    def __init__(self, config_path: str = "src/config/config.yaml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load YAML configuration
        self.config_path = config_path
        self.config = self._load_config()
        
        # Replace environment variable placeholders in config
        self._process_env_vars()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Dict containing configuration settings
        """
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {}
    
    def _process_env_vars(self):
        """
        Process configuration values to replace ${ENV_VAR} placeholders
        with actual environment variable values.
        """
        def _replace_env_vars(obj):
            if isinstance(obj, dict):
                return {k: _replace_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_replace_env_vars(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                return os.environ.get(env_var, f"MISSING_ENV_VAR_{env_var}")
            return obj
        
        self.config = _replace_env_vars(self.config)
    
    def get(self, key: str, default=None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: The configuration key (can use dot notation for nested keys)
            default: Default value if key not found
        
        Returns:
            Configuration value or default if not found
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_batches(self) -> List[str]:
        """
        Get the list of YC batches to scrape.
        
        Returns:
            List of batch identifiers (e.g., ["W25", "S24"])
        """
        return self.get('batches', [])
    
    def get_selectors(self) -> Dict[str, str]:
        """
        Get the CSS selectors for scraping.
        
        Returns:
            Dict of selector names to CSS selector strings
        """
        return self.get('scraper.selectors', {})
    
    def get_classification_prompt(self) -> str:
        """
        Get the LLM classification prompt template.
        
        Returns:
            Prompt template string
        """
        return self.get('analyzer.classification_prompt', '')
    
    def get_csv_columns(self) -> List[str]:
        """
        Get the column names for CSV export.
        
        Returns:
            List of column names
        """
        return self.get('notion.csv_columns', []) 