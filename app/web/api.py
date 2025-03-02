from fastapi import FastAPI, HTTPException
from app.database.db import RegulationDAO
from app.analysis.ecfr_analyzer import eCFRAnalyzer
from main import ECFRMonitor
from typing import Dict, List, Any

app = FastAPI(title="eCFR Analyzer API")
dao = RegulationDAO()
analyzer = eCFRAnalyzer(dao)
monitor = ECFRMonitor()

@app.get("/agencies", response_model=List[Dict[str, Any]])
async def get_agencies():
    return monitor.get_agencies()

@app.get("/titles/{agency_slug}", response_model=List[int])
async def get_titles(agency_slug: str):
    return monitor.get_titles_for_agency(agency_slug)

@app.post("/monitor/{agency_slug}/{title}")
async def monitor_agency_title(agency_slug: str, title: str, start_date: str, end_date: str):
    await monitor.monitor_agency_title(agency_slug, title, start_date, end_date)
    return {"message": f"Monitoring started for agency {agency_slug}, title {title}, from {start_date} to {end_date}"}

@app.get("/word_count_per_agency", response_model=Dict[str, int])
async def get_word_count_per_agency():
    result = analyzer.word_count_per_agency()
    return result if result is not None else {}

@app.get("/historical_changes", response_model=List[List[Any]])
async def get_historical_changes(start_date: str, end_date: str):
    result = analyzer.historical_changes_over_time(start_date, end_date)
    return result if result is not None else []

@app.get("/keywords", response_model=List[tuple])
async def get_keywords():
    result = analyzer.keywords_analysis()
    return result if result is not None else []