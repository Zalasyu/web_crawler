from app.database.db import RegulationDAO
from collections import Counter
import re
import requests
from typing import Dict, List, Any
from loguru import logger

logger.remove()
logger.add("ecfr_analyzer.log", level="DEBUG", format="{time} {level} {message}")
logger.add(lambda msg: print(msg, end=""), level="INFO", colorize=True)


class eCFRAnalyzer:
    def __init__(self, dao: RegulationDAO):
        self.dao = dao
        self.base_url = "https://www.ecfr.gov"

    def _get_agency_mapping(self):
        response = requests.get(f"{self.base_url}/api/admin/v1/agencies.json")
        response.raise_for_status()
        agencies = response.json().get("agencies", [])
        title_to_agency = {}
        for agency in agencies:
            agency_name = agency["display_name"]
            for ref in agency.get("cfr_references", []):
                title = str(ref["title"])
                title_to_agency[title] = agency_name
        return title_to_agency

    def word_count_per_agency(self) -> Dict[str, int]:
        with self.dao as cursor:
            cursor.execute("SELECT title, content FROM regulations WHERE section_id = 'full'")
            results = cursor.fetchall()
            if not results:
                logger.warning("No regulation data found for word count.")
                return {}
            title_to_agency = self._get_agency_mapping()
            word_counts = {}
            for title, content in results:
                agency = title_to_agency.get(str(title), f"Unknown (Title {title})")
                words = len(re.findall(r'\w+', content))
                word_counts[agency] = word_counts.get(agency, 0) + words
            for agency in title_to_agency.values():
                if agency not in word_counts:
                    word_counts[agency] = 0
            logger.debug(f"Word counts calculated: {word_counts}")
            return word_counts

    def historical_changes_over_time(self, start_date: str, end_date: str) -> List[List[Any]]:
        with self.dao as cursor:
            cursor.execute("""
                SELECT date, COUNT(*) 
                FROM changes 
                WHERE date BETWEEN ? AND ? 
                GROUP BY date 
                ORDER BY date
            """, (start_date, end_date))
            results = cursor.fetchall()
            if not results:
                logger.warning(f"No changes found between {start_date} and {end_date}")
                return []
            return [[row[0], row[1]] for row in results]

    def keywords_analysis(self) -> List[tuple]:
        with self.dao as cursor:
            cursor.execute("SELECT content FROM regulations WHERE section_id = 'full'")
            results = cursor.fetchall()
            if not results:
                return []
            all_text = " ".join(row[0] for row in results)
            words = re.findall(r'\w+', all_text.lower())
            common = Counter(words).most_common(10)
            return common