from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager
from src.exporter.csv_exporter import CSVExporter

config = ConfigManager()
db = DatabaseManager()
exporter = CSVExporter(config, db)

# Export all companies
csv_path = exporter.export_all_companies("yc_companies_export.csv")
print(f"Data exported to: {csv_path}") 