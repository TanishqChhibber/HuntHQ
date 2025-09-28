import csv
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

OUTPUT_CSV = 'data/wipro_jobs.csv'
WIPRO_URL = 'https://careers.wipro.com/search/?q=&locationsearch=india&searchResultView=LIST&pageNumber=0&facetFilters=%7B%7D&sortBy=&markerViewed=&carouselIndex='


def _chrome():
    opts = Options()
    headless = os.getenv('HEADLESS', '1') != '0'
    if headless:
        opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--user-agent=Mozilla/5.0')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def _dismiss_cookies(driver):
    try:
        banner = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.cookiePolicy.cookiemanager')))
        if banner.is_displayed():
            btn = banner.find_elements(By.ID, 'cookie-accept')
            if btn:
                driver.execute_script('arguments[0].click();', btn[0])
                time.sleep(0.3)
    except Exception:
        pass


def _split_multi(val: str):
    if not val:
        return []
    # Split on ; or , while preserving meaningful tokens
    parts = [p.strip() for chunk in val.split(';') for p in chunk.split(',')]
    return [p for p in parts if p]


def _norm_join(parts):
    # Join back with '; ' for consistent CSV representation
    return '; '.join(dict.fromkeys(parts))  # preserve order & uniqueness


def scrape_wipro(progress_callback=None, expand_multi=False, fetch_details=False):
    """Scrape Wipro India jobs list view and save required columns.
    expand_multi: if True, create one row per city/state combination when multiple listed.
    fetch_details: if True, attempt to open each job link (slower) to refine category (placeholder hook).
    """
    def report(p, m):
        if progress_callback:
            progress_callback(p, m)
    rows = []
    driver = None
    try:
        report(5, 'Launching browser')
        driver = _chrome()
        driver.get(WIPRO_URL)
        wait = WebDriverWait(driver, 30)
        report(15, 'Loading job cards')
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li[data-testid="jobCard"]')))
        _dismiss_cookies(driver)
        page = 0
        seen_ids = set()
        while True:
            cards = driver.find_elements(By.CSS_SELECTOR, 'li[data-testid="jobCard"]')
            if not cards:
                break
            for card in cards:
                try:
                    try:
                        a = card.find_element(By.CSS_SELECTOR, 'a.jobCardTitle')
                    except Exception:
                        a = card.find_element(By.CSS_SELECTOR, 'a')
                    title = a.text.strip()
                    apply_link = a.get_attribute('href')
                    spans = card.find_elements(By.CSS_SELECTOR, 'span.JobsList_jobCardFooterValue__Lc--j')
                    if not spans:
                        spans = card.find_elements(By.CSS_SELECTOR, 'span')
                    vals = [s.text.strip() for s in spans if s.text.strip()]
                    job_id = vals[0] if len(vals) > 0 else ''
                    raw_city = vals[1] if len(vals) > 1 else ''
                    raw_state = vals[2] if len(vals) > 2 else ''
                    country = vals[3] if len(vals) > 3 else ''
                    category = vals[4] if len(vals) > 4 else ''
                    if not (title and job_id.isdigit()) or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    cities = _split_multi(raw_city)
                    states = _split_multi(raw_state)
                    norm_city = _norm_join(cities) if cities else raw_city
                    norm_state = _norm_join(states) if states else raw_state

                    # Optional detail fetch hook (currently placeholder)
                    if fetch_details and not category:
                        # Could navigate to apply_link in a new tab and parse extra fields
                        pass

                    base_row = {
                        'Job Title': title,
                        'Job ID': job_id,
                        'Country': country,
                        'Category': category,
                        'Apply Link': apply_link,
                        'Scraped At': datetime.utcnow().isoformat()
                    }

                    if expand_multi and cities and states:
                        # Cartesian product city/state (aligned with provided example style)
                        for c in cities:
                            for s in states:
                                rows.append({**base_row, 'City': c, 'State': s})
                    else:
                        rows.append({**base_row, 'City': norm_city, 'State': norm_state})
                except Exception:
                    continue
            report(min(85, 25 + page * 10), f'Collected {len(rows)} jobs (page {page+1})')
            # Pagination attempts
            advanced_break = True
            try:
                next_btn = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="goToNextPageBtn"]'))
                )
                if next_btn.is_enabled() and not next_btn.get_attribute('disabled'):
                    advanced_break = False
                    try:
                        driver.execute_script('arguments[0].click();', next_btn)
                    except ElementClickInterceptedException:
                        driver.execute_script('arguments[0].click();', next_btn)
                    time.sleep(1.3)
                    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li[data-testid="jobCard"]')))
                    _dismiss_cookies(driver)
                    page += 1
            except TimeoutException:
                pass
            if advanced_break:
                break
        if not os.path.exists('data'):
            os.makedirs('data')
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Job Title','Job ID','City','State','Country','Category','Apply Link','Scraped At'])
            writer.writeheader()
            writer.writerows(rows)
        report(100, f'Done: {len(rows)} jobs')
        return rows
    except Exception as e:
        report(100, f'Error: {e}')
        return rows
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    data = scrape_wipro(expand_multi=False)
    print(f'Scraped {len(data)} jobs -> {OUTPUT_CSV}')
