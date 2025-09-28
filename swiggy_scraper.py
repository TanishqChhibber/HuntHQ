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
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def scrape_swiggy(progress_callback=None):
    """Single Swiggy scraper used by the Flask app.
    Returns True on success, False otherwise.
    """
    def report(p, m):
        if progress_callback:
            progress_callback(p, m)

    report(10, 'Setting up headless browser')
    jobs = []
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0')
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        url = 'https://careers.swiggy.com/#/careers'
        report(15, 'Navigating to careers page')
        driver.get(url)
        wait = WebDriverWait(driver, 30)

        # Switch to iframe
        try:
            iframe = wait.until(EC.presence_of_element_located((By.ID, 'mnhembedded')))
            driver.switch_to.frame(iframe)
        except TimeoutException:
            report(100, 'Iframe not found - no jobs')
            return False

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.mnh-jobs-table-row')))
        report(25, 'Job table loaded')

        page = 1
        while True:
            rows = driver.find_elements(By.CSS_SELECTOR, 'tr.mnh-jobs-table-row')
            for r in rows:
                try:
                    title = r.find_element(By.CSS_SELECTOR, 'span.mnh_req_title').text.strip()
                except NoSuchElementException:
                    continue
                try:
                    location = r.find_element(By.CSS_SELECTOR, 'span.mnh_location').text.strip()
                except NoSuchElementException:
                    location = 'N/A'
                try:
                    a = r.find_element(By.CSS_SELECTOR, 'a[href]')
                    link = a.get_attribute('href')
                except NoSuchElementException:
                    link = url
                jobs.append({
                    'Timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'Role': title,
                    'Location': location,
                    'Company': 'Swiggy',
                    'Category': 'N/A',
                    'Job Link': link,
                    'Responsibilities': 'Visit link',
                    'Qualifications': 'Visit link',
                    'Apply Link': link
                })
            report(min(80, 25 + page * 5), f'Collected {len(jobs)} jobs (page {page})')

            # Pagination: look for next page number
            next_num = page + 1
            next_links = driver.find_elements(By.XPATH, "//a[not(contains(@class,'disabled')) and string(number(text()))=text()]")
            moved = False
            for l in next_links:
                if l.text.strip() == str(next_num):
                    driver.execute_script('arguments[0].click();', l)
                    time.sleep(2)
                    page += 1
                    moved = True
                    break
            if not moved:
                break

        if not os.path.exists('data'):
            os.makedirs('data')
        pd.DataFrame(jobs).to_csv('data/swiggy_jobs.csv', index=False)
        report(85, f'Saved {len(jobs)} jobs to CSV')
        return True if jobs else False
    except Exception as e:
        print('Scrape error:', e)
        report(100, f'Error: {e}')
        return False
    finally:
        if driver:
            driver.quit()

# Allow standalone run
if __name__ == '__main__':
    ok = scrape_swiggy()
    print('Done. Success:' , ok)
