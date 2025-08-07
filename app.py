from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import pandas as pd
from datetime import datetime
import threading
import uuid
import sys
import traceback

app = Flask(__name__)

# Store scraping results temporarily
scraping_results = {}
scraping_status = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    data = request.get_json()
    company = data.get('company', '').lower().strip()
    
    if not company:
        return jsonify({'error': 'Company name is required'}), 400
    
    if company not in ['swiggy']:
        return jsonify({'error': f'Scraper for "{company}" not available yet. Currently supported: swiggy'}), 400
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    scraping_status[task_id] = {'status': 'running', 'progress': 0, 'message': 'Starting scraper...'}
    
    # Start scraping in background thread
    thread = threading.Thread(target=run_scraper, args=(company, task_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})

@app.route('/api/status/<task_id>')
def get_status(task_id):
    if task_id not in scraping_status:
        return jsonify({'error': 'Task not found'}), 404
    
    status = scraping_status[task_id]
    if status['status'] == 'completed' and task_id in scraping_results:
        status['results'] = scraping_results[task_id]
    
    return jsonify(status)

@app.route('/api/test-jobs')
def test_jobs():
    """Test endpoint to check if job data is being read correctly"""
    try:
        csv_path = 'data/swiggy_jobs.csv'
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            results = df.to_dict('records')
            return jsonify({
                'status': 'success',
                'count': len(results),
                'jobs': results
            })
        else:
            return jsonify({'error': 'No job data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<task_id>')
def download_csv(task_id):
    if task_id not in scraping_results:
        return jsonify({'error': 'No results found for this task'}), 404
    
    results = scraping_results[task_id]
    if not results:
        return jsonify({'error': 'No jobs found to download'}), 404
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)
    csv_filename = f"jobs_{task_id}.csv"
    csv_path = os.path.join('data', csv_filename)
    
    if not os.path.exists('data'):
        os.makedirs('data')
    
    df.to_csv(csv_path, index=False)
    
    return send_file(csv_path, as_attachment=True, download_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

def run_scraper(company, task_id):
    try:
        scraping_status[task_id]['message'] = 'Initializing scraper...'
        scraping_status[task_id]['progress'] = 10
        
        if company == 'swiggy':
            scraping_status[task_id]['message'] = 'Scraping Swiggy jobs...'
            scraping_status[task_id]['progress'] = 30
            
            # Import the scraper functions
            try:
                from swiggy_scraper import scrape_swiggy_selenium, scrape_swiggy
                
                # Try Selenium scraping first
                success = scrape_swiggy_selenium()
                
                # If Selenium fails, try traditional scraping
                if not success:
                    scraping_status[task_id]['message'] = 'Trying traditional scraping...'
                    scraping_status[task_id]['progress'] = 60
                    scrape_swiggy()
                    
            except ImportError as e:
                scraping_status[task_id]['message'] = 'Scraper modules not found, using basic scraping...'
                scraping_status[task_id]['progress'] = 50
                # Create a basic entry if scraper is not available
                if not os.path.exists("data"):
                    os.makedirs("data")
                
                sample_data = [{
                    "Timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "job_id": 1,
                    "Role": f"Sample Job for {company.title()}",
                    "Company": company.title(),
                    "Logo": f"https://careers.{company}.com/favicon.ico",
                    "Location": "Multiple Cities",
                    "Experience": "Not specified",
                    "Salary": "Not disclosed",
                    "Job Link": f"https://careers.{company}.com/#/careers",
                    "Posted By (LinkedIn URL)": "",
                    "Employment Type": "Full-time",
                    "Scout": "No",
                    "Skills": "Check website for details"
                }]
                
                df = pd.DataFrame(sample_data)
                df.to_csv(f"data/{company}_jobs.csv", index=False)
            
            scraping_status[task_id]['progress'] = 80
            scraping_status[task_id]['message'] = 'Processing results...'
            
            # Read the results from CSV if available
            csv_path = f'data/{company}_jobs.csv'
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                results = df.to_dict('records')
                scraping_results[task_id] = results
                
                scraping_status[task_id]['status'] = 'completed'
                scraping_status[task_id]['progress'] = 100
                scraping_status[task_id]['message'] = f'Successfully scraped {len(results)} jobs!'
            else:
                scraping_status[task_id]['status'] = 'completed'
                scraping_status[task_id]['progress'] = 100
                scraping_status[task_id]['message'] = 'No jobs found or scraping failed'
                scraping_results[task_id] = []
        
    except Exception as e:
        scraping_status[task_id]['status'] = 'error'
        scraping_status[task_id]['message'] = f'Error: {str(e)}'
        print(f"Scraping error: {traceback.format_exc()}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
