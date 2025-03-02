from app.database.db import RegulationDAO
import hashlib
from bs4 import BeautifulSoup

class ECFRService:
    def __init__(self, regulation_dao: RegulationDAO):
        self.regulation_dao = regulation_dao

    def calculate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def store_regulation(self, title: str, section_id: str, date: str, content: str):
        hash_value = self.calculate_hash(content)
        self.regulation_dao.insert_regulation(title, section_id, date, hash_value, content)

    def track_changes(self, title: str, date: str, old_content: str, new_content: str):
        soup_old = BeautifulSoup(old_content, 'xml')
        soup_new = BeautifulSoup(new_content, 'xml')
        
        # Use <DIV8> for section-level changes as per guide
        old_sections = {div.get('N', 'full'): str(div) for div in soup_old.find_all('DIV8', TYPE='SECTION')}
        if not old_sections:
            old_sections['full'] = old_content

        new_sections = {div.get('N', 'full'): str(div) for div in soup_new.find_all('DIV8', TYPE='SECTION')}
        if not new_sections:
            new_sections['full'] = new_content

        all_section_ids = set(old_sections.keys()) | set(new_sections.keys())
        for section_id in all_section_ids:
            old_text = old_sections.get(section_id, "")
            new_text = new_sections.get(section_id, "")
            old_hash = self.calculate_hash(old_text) if old_text else None
            new_hash = self.calculate_hash(new_text) if new_text else None
            if old_hash != new_hash:
                self.regulation_dao.insert_change(title, section_id, date, old_hash, new_hash)