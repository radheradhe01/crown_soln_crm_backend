import csv
import codecs
from typing import List, Dict, Any, Generator

def parse_csv(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Parse CSV content into a list of dictionaries.
    """
    decoded_content = file_content.decode("utf-8")
    csv_reader = csv.DictReader(decoded_content.splitlines())
    
    results = []
    for row in csv_reader:
        # Clean keys and values
        clean_row = {k.strip(): v.strip() for k, v in row.items() if k}
        results.append(clean_row)
        
    return results
