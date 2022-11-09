import json
import os.path
from spiders import generic_scraper

input_config = "investis_config.json"
main_base = os.path.dirname(__file__)
config_file_path = os.path.join(main_base, "config_files", input_config)
if __name__ == '__main__':
    with open(config_file_path, 'r') as config_file:
        config_data = json.load(config_file)
        scraper = generic_scraper.BaseClass(config_data)
        scraper.extract_data()