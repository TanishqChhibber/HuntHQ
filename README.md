# HuntHQ

Lightweight Flask-based job scraping service + minimal frontend UI.

Currently supported companies (live):
- Swiggy
- Wipro

## Overview
The app exposes an HTTP API and a single-page HTML interface (`templates/index.html`) that lets a user trigger a background scrape job for a supported company, poll progress, view results, and download a CSV.

Scrapers use Selenium (headless Chrome) to navigate dynamic career sites (iframes / pagination) and extract structured job data.

## Features
- Background scraping threads (non-blocking HTTP requests)
- Progress polling endpoint (`/api/status/<task_id>`)
- CSV download for completed tasks
- Unified in-memory status/result store (prototype)
- Swiggy scraper: role, location, apply link, basic placeholders for details
- Wipro scraper: job id, title, city/state normalization, category, apply link, optional multi-location expansion (parameter inside code)

## Project Structure
```
app.py                # Flask API + task management
swiggy_scraper.py     # Swiggy Selenium scraper
wipro_scraper.py      # Wipro Selenium scraper (enhanced normalization)
templates/index.html  # Frontend UI
requirements.txt      # Dependencies
/data                 # Output CSVs (created at runtime)
```

## API Endpoints
| Method | Path                  | Description |
|--------|-----------------------|-------------|
| POST   | /api/scrape           | Start a scrape. JSON body: {"company": "swiggy"|"wipro"} |
| GET    | /api/status/<task_id> | Poll scrape status & retrieve results once completed |
| GET    | /api/download/<task_id> | Download CSV for that task |
| GET    | /                    | Web UI |

### Status Object
```
{
  "status": "running" | "completed" | "error",
  "progress": 0-100,
  "message": "human readable stage",
  "results": [ ... ]          # only when completed
}
```

## Running Locally
1. Create / activate a virtual environment (optional but recommended).
2. Install requirements:
```
pip install -r requirements.txt
```
3. Run the app:
```
python app.py
```
4. Open: http://127.0.0.1:5000/
5. Enter a supported company (swiggy or wipro) and start.

## Scraper Notes
### Swiggy
- Navigates to careers portal, switches to iframe `mnhembedded`.
- Iterates paginated job table rows.
- Extracts: Timestamp, Role, Location, Company, Category (placeholder), Job/Apply Link.

### Wipro
- Navigates directly to India search results list view.
- Extracts footer span sequence: Job ID, City, State, Country, Category.
- Deduplicates by Job ID.
- Multi-value city/state fields are normalized (semicolon separated).
- Optional expansion & detail fetch flags are present in `scrape_wipro()` (currently called with defaults). Adjust in `app.py` if extending.

## Environment Variables
| Name      | Purpose                                  | Default |
|-----------|-------------------------------------------|---------|
| HEADLESS  | Set to `0` to see browser (Wipro/Swiggy)  | `1`     |

Example (show browser while debugging):
```
HEADLESS=0 python app.py
```

## Adding Another Company (Future Roadmap)
1. Create `newcompany_scraper.py` exposing `scrape_newcompany(progress_callback=...)` returning success / writing CSV to `data/<company>_jobs.csv`.
2. Add company key to `allowed` set in `app.py` and import branch in `run_scraper`.
3. Update UI supported companies list.

## Limitations / TODO
- In-memory result storage (lost on restart) -> replace with Redis or DB for production.
- No authentication / rate limiting.
- Error details not surfaced to frontend beyond generic message.
- Category enrichment for Swiggy minimal; Wipro detail fetch placeholder inactive.
- No automated tests yet.

## Disclaimer
This project is for educational / internal research use. Ensure scraping complies with each site's Terms of Service and robots policies. Add delays or caching to reduce load if scaling.

## License
(Choose and add a license file if you intend to open source.)

---
Maintained for Swiggy + Wipro only at this stage.
