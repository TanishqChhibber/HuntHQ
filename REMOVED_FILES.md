Removed legacy / unused files for project simplification:

- api_runner.py (legacy direct API POST approach)
- hunthq.py (CLI interface superseded by Flask app)
- swiggy_gemini.py (older experimental scraper)
- swiggy_scraper_clean.py (empty)
- swiggy_scraper_final.py (large multi-format scraper; replaced with simplified swiggy_scraper.py)
- wipro_scraper.py (separate Wipro scraper not needed for current single-company scope)
- clean_wipro_csv.py (data cleaning script no longer required)

Retained:
- app.py (simplified Flask API)
- swiggy_scraper.py (single unified Swiggy scraper)
- templates/index.html (frontend)
- requirements.txt
- data/ (existing CSV outputs)

Update rationale:
Focus on a minimal working vertical slice: user triggers scrape for Swiggy via web UI -> background thread runs unified Selenium scraper -> results downloadable.

Removed files listed here have now been deleted. Current minimal codebase retained.
