# hunthq.py

from swiggy_scraper import scrape_swiggy

def main():
    print("=== Welcome to HuntHQ 🔎 ===")
    print("Supported companies: swiggy")
    company = input("Enter company name: ").strip().lower()

    if company == "swiggy":
        print("\n[🎯] Starting Swiggy job scraping...")
        
        # Try traditional scraping first
        scrape_swiggy()
        
        # Ask user if they want to try advanced Selenium scraping
        try_selenium = input("\n[🤖] Would you like to try Selenium-based scraping for more results? (y/n): ").strip().lower()
        
        if try_selenium == 'y':
            try:
                from swiggy_scraper import scrape_swiggy_selenium
                scrape_swiggy_selenium()
            except ImportError:
                print("[ℹ️] Selenium functions not available. Make sure all dependencies are installed.")
            except Exception as e:
                print(f"[⚠️] Error with Selenium scraping: {e}")
    else:
        print(f"[❌] Scraper for '{company}' not available yet.")

if __name__ == "__main__":
    main()
