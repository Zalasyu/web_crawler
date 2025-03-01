import requests
import datetime
import hashlib
from database import RegulationDAO

BASE_URL = "https://www.ecfr.gov/api/versioner/v1"

class ECFRService:
    def __init__(self, regulation_dao: RegulationDAO):
        self.regulation_dao = regulation_dao

    def get_titles(self):
        url = f"{BASE_URL}/titles.json"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_versions(self, title):
        url = f"{BASE_URL}/versions/title-{title}.json"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_content(self, title, version, date):
        url = f"{BASE_URL}/full/{date}/title-{title}.xml"
        if "section" in version or "appendix" in version:
            url = f"{BASE_URL}/full/{date}/title-{title}/{version}.xml"

        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def calculate_hash(self, content):
        return hashlib.sha256(content.encode()).hexdigest()

    def store_regulation(self, title, version, date, content):
        hash_value = self.calculate_hash(content)
        self.regulation_dao.insert_regulation(title, version, date, hash_value, content)

    def track_changes(self, title, version, date, content):
        hash_value = self.calculate_hash(content)
        previous_hash = self.regulation_dao.get_regulation_hash(title, version)

        if previous_hash and hash_value != previous_hash:
            print(f"Change detected: Title={title}, Version={version}, Date={date}")
            self.regulation_dao.insert_change(title, version, date, previous_hash, hash_value)