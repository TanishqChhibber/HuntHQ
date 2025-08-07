# swiggy_scraper.py

import pandas as pd
from datetime import datetime
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

def scrape_swiggy():
    """
    Main Swiggy scraper - gets all real job listings with complete details.
    """
    print("[🎯] Starting Swiggy job scraper to get ALL REAL JOBS...")
    
    all_jobs = []
    driver = None
    try:
        print("[🚀] Using Selenium to get REAL job data...")
        
        # Setup Chrome options for headless Browse
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
        print("🔧 Setting up Chrome driver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        url = "https://careers.swiggy.com/#/careers"
        print(f"🌐 Navigating to URL: {url}")
        driver.get(url)
    
        # Wait for iframe to appear and switch to it
        wait = WebDriverWait(driver, 30)
        try:
            iframe = wait.until(EC.presence_of_element_located((By.ID, "mnhembedded")))
            print("[DEBUG] Found jobs iframe. Switching to iframe...")
            driver.switch_to.frame(iframe)
        except TimeoutException:
            print("❌ Jobs iframe did not load within the expected time. Exiting.")
            return
        
        # Wait for the job listings to load inside the iframe
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr.mnh-jobs-table-row")))
        print("✅ Job listings have loaded inside the iframe!")
        
        print("📄 Starting job extraction (with pagination)...")
        page_num = 1
        
        while True:
            # Re-find job rows on the current page to avoid stale element references
            job_rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.mnh-jobs-table-row")))
            print(f"🔍 [Page {page_num}] Found {len(job_rows)} job elements.")
    
            # Process ALL jobs on current page using index-based approach to handle DOM changes
            jobs_processed = 0
            row_idx = 0
            while row_idx < len(job_rows):
                try:
                    # Always re-find job rows to handle any DOM changes
                    current_job_rows = driver.find_elements(By.CSS_SELECTOR, "tr.mnh-jobs-table-row")
                    if row_idx >= len(current_job_rows):
                        print(f"  [INFO] Only {len(current_job_rows)} jobs available, breaking")
                        break
                    
                    row = current_job_rows[row_idx]
                    
                    # Extract basic job info first
                    try:
                        title_elem = row.find_element(By.CSS_SELECTOR, "span.mnh_req_title")
                        title = title_elem.text.strip()
                    except NoSuchElementException:
                        print(f"  [SKIP] No title found for row {row_idx}")
                        row_idx += 1
                        continue
                    
                    try:
                        location_elem = row.find_element(By.CSS_SELECTOR, "span.mnh_location")
                        location = location_elem.text.strip()
                    except NoSuchElementException:
                        location = "N/A"
                    
                    # Handle missing job link gracefully
                    try:
                        job_link = row.find_element(By.CSS_SELECTOR, "a[href]").get_attribute("href")
                    except NoSuchElementException:
                        job_link = url  # Use the main careers URL as fallback

                    all_jobs.append({
                        "Timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "Role": title,
                        "Location": location,
                        "Company": "Swiggy",
                        "Category": "N/A",
                        "Job Link": job_link,
                        "Responsibilities": "Visit job link for details",
                        "Qualifications": "Visit job link for details", 
                        "Apply Link": job_link
                    })
                    print(f"✅ Extracted: {title} at {location} (page {page_num})")
                    jobs_processed += 1

                except Exception as e:
                    print(f"⚠️ An error occurred while processing a job row (page {page_num}, row {row_idx}): {str(e)[:100]}...")
                
                row_idx += 1
            
            print(f"📊 Processed {jobs_processed} jobs on page {page_num}")
    
            # --- Pagination Logic - Look for numbered page links ---
            try:
                # Find all numbered page links that are not disabled and not active
                page_links = driver.find_elements(By.XPATH, "//a[not(contains(@class, 'disabled')) and not(contains(@class, 'active')) and string(number(text()))=text()]")
                
                # Look for the next page number
                next_page_num = page_num + 1
                next_page_found = False
                
                for link in page_links:
                    if link.is_displayed() and link.text.strip() == str(next_page_num):
                        print(f"➡️ Clicking to page {next_page_num}...")
                        driver.execute_script("arguments[0].scrollIntoView(true);", link)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", link)
                        time.sleep(5) # Wait for the new page to load
                        page_num += 1
                        next_page_found = True
                        break
                
                if not next_page_found:
                    print("⏹️ No more pages found. Finished pagination.")
                    break
                    
            except Exception as e:
                print(f"⏹️ Pagination error: {e}. Finished pagination.")
                break
    
    except Exception as e:
        print(f"❌ An error occurred during scraping: {e}")
    finally:
        if driver:
            driver.quit()
            print("🔒 Browser closed.")
    
    if all_jobs:
        if not os.path.exists("data"):
            os.makedirs("data")
        df = pd.DataFrame(all_jobs)
        df.to_csv("data/swiggy_jobs.csv", index=False)
        print(f"🎉 Scraped {len(all_jobs)} jobs from all pages and saved to data/swiggy_jobs.csv")
    else:
        print("❌ No jobs could be extracted. Please check the website's structure.")
        
if __name__ == "__main__":
    scrape_swiggy()