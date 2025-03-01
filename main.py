import datetime
import requests
from app.database.db import RegulationDAO
from app.retrieval.ecfr_service import ECFRService

def main():
    regulation_dao = RegulationDAO()
    regulation_dao.create_tables()  # Create tables only once

    ecfr_service = ECFRService(regulation_dao)
    today = datetime.date.today().strftime("%Y-%m-%d")
    titles = ecfr_service.get_titles()

    for title_data in titles:
        title = title_data["title"]
        versions = ecfr_service.get_versions(title)
        for version_data in versions:
            version = version_data["version"]
            try:
                content = ecfr_service.get_content(title, version, today)
                ecfr_service.store_regulation(title, version, today, content)
                ecfr_service.track_changes(title, version, today, content)
            except requests.exceptions.HTTPError as e:
                print(f"Error retrieving content for Title={title}, Version={version}: {e}")

if __name__ == "__main__":
    main()