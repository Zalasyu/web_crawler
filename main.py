import asyncio
import aiohttp
from loguru import logger
from pprint import pformat
from app.database.db import RegulationDAO
from app.retrieval.ecfr_service import ECFRService
import requests
from datetime import datetime, timedelta
from aiohttp import ClientSession, ClientResponseError
from bs4 import BeautifulSoup

logger.remove()
logger.add("ecfr_monitor.log", level="DEBUG", format="{time} {level} {message}")
logger.add(lambda msg: print(msg, end=""), level="INFO", colorize=True)

class ECFRMonitor:
    """Class to monitor eCFR titles with versioning and rate limiting."""
    
    def __init__(self):
        self.regulation_dao = RegulationDAO()
        self.ecfr_service = ECFRService(self.regulation_dao)
        self.base_url = "https://www.ecfr.gov"
        self.semaphore = asyncio.Semaphore(10)

    def setup_database(self):
        self.regulation_dao.create_tables()
        logger.info("Database tables created or verified.")

    def get_agencies(self):
        logger.debug("Fetching agencies from eCFR API...")
        response = requests.get(f"{self.base_url}/api/admin/v1/agencies.json")
        response.raise_for_status()
        return response.json().get("agencies", [])

    def get_titles_for_agency(self, agency_slug: str):
        agencies = self.get_agencies()
        titles = set()
        for agency in agencies:
            if agency["slug"] == agency_slug:
                for ref in agency.get("cfr_references", []):
                    titles.add(ref["title"])
                return list(titles)
        logger.warning(f"Agency {agency_slug} not found.")
        return []

    def get_all_titles(self):
        response = requests.get(f"{self.base_url}/api/versioner/v1/titles.json")
        response.raise_for_status()
        return [str(title["number"]) for title in response.json().get("titles", [])]

    async def fetch_content_with_retry(self, session: ClientSession, title: str, date: str, retries: int = 3):
        url = f"{self.base_url}/api/versioner/v1/full/{date}/title-{title}.xml"
        for attempt in range(retries):
            try:
                async with self.semaphore:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        content = await response.text()
                        new_hash = self.ecfr_service.calculate_hash(content)
                        logger.debug(f"Fetched content for Title={title}, Date={date}, Hash={new_hash}")
                        return title, date, content, new_hash
            except ClientResponseError as e:
                if e.status == 429:
                    wait_time = 2 ** attempt
                    logger.warning(f"429 Too Many Requests for {url}, retrying in {wait_time}s (attempt {attempt + 1}/{retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url}: {e}")
                    return title, date, None, None
        logger.error(f"Max retries reached for {url}")
        return title, date, None, None

    async def monitor_content(self, title: str, date: str, prev_content: str = None):
        async with aiohttp.ClientSession() as session:
            title, date, content, new_hash = await self.fetch_content_with_retry(session, title, date)
            if content:
                if prev_content:
                    self.ecfr_service.track_changes(title, date, prev_content, content)
                self.ecfr_service.store_regulation(title, "full", date, content)
                return content
            return None

    async def monitor_agency_title(self, agency_slug: str, title: str, start_date: str, end_date: str):
        self.setup_database()
        titles = self.get_titles_for_agency(agency_slug)
        if int(title) not in titles:
            logger.error(f"Title {title} not associated with agency {agency_slug}")
            return

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start
        prev_content = None

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            prev_content = await self.monitor_content(title, date_str, prev_content)
            current += timedelta(days=1)

        logger.info(f"Completed monitoring Title={title} for agency {agency_slug} from {start_date} to {end_date}")

    async def preload_all_titles(self, date: str):
        """Preload all titles for a given date to ensure word count reflects all agencies."""
        all_titles = self.get_all_titles()
        tasks = []
        async with aiohttp.ClientSession() as session:
            for title in all_titles:
                tasks.append(self.fetch_content_with_retry(session, title, date))
            results = await asyncio.gather(*tasks)
            for title, date, content, new_hash in results:
                if content:
                    self.ecfr_service.store_regulation(title, "full", date, content)

def main():
    monitor = ECFRMonitor()
    # Preload all titles for a baseline (optional, run once)
    asyncio.run(monitor.preload_all_titles("2025-02-01"))
    # Monitor specific agency title for changes
    asyncio.run(monitor.monitor_agency_title("agriculture-department", "7", "2025-02-10", "2025-02-12"))

if __name__ == "__main__":
    main()