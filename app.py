from flask import Flask, render_template, request, jsonify, send_file
import os
import pandas as pd
from datetime import datetime
import threading
import uuid
import traceback

app = Flask(__name__)

# In‑memory stores (simple prototype; not for production concurrency)
scraping_results = {}
scraping_status = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    data = request.get_json() or {}
    company = data.get('company', '').lower().strip()
    allowed = {'swiggy', 'wipro'}
    if company not in allowed:
        return jsonify({'error': f'Only supported: {", ".join(sorted(allowed))}'}), 400

    task_id = str(uuid.uuid4())
    scraping_status[task_id] = {'status': 'running', 'progress': 0, 'message': 'Queued', 'company': company}

    thread = threading.Thread(target=run_scraper, args=(company, task_id), daemon=True)
    thread.start()
    return jsonify({'task_id': task_id, 'status': 'started'})

@app.route('/api/status/<task_id>')
def get_status(task_id):
    status = scraping_status.get(task_id)
    if not status:
        return jsonify({'error': 'Task not found'}), 404
    if status['status'] == 'completed':
        status = {**status, 'results': scraping_results.get(task_id, [])}
    return jsonify(status)

@app.route('/api/download/<task_id>')
def download_csv(task_id):
    if task_id not in scraping_results:
        return jsonify({'error': 'No results for this task'}), 404
    rows = scraping_results[task_id]
    if not rows:
        return jsonify({'error': 'No data to download'}), 404
    if not os.path.exists('data'):
        os.makedirs('data')
    csv_path = os.path.join('data', f'jobs_{task_id}.csv')
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    return send_file(csv_path, as_attachment=True, download_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")


def run_scraper(company: str, task_id: str):
    try:
        scraping_status[task_id].update(message='Initializing...', progress=5)
        if company == 'swiggy':
            from swiggy_scraper import scrape_swiggy as runner
        elif company == 'wipro':
            from wipro_scraper import scrape_wipro as runner
        else:
            scraping_status[task_id].update(status='error', message='Unsupported company')
            return

        scraping_status[task_id].update(message='Launching browser...', progress=15)
        success = runner(progress_callback=lambda p, m: _update_progress(task_id, p, m))

        scraping_status[task_id].update(message='Reading results...', progress=90)
        csv_path = f'data/{company}_jobs.csv'
        if success and os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            scraping_results[task_id] = df.to_dict('records')
            scraping_status[task_id].update(status='completed', progress=100, message=f'Successfully scraped {len(df)} jobs')
        else:
            scraping_results[task_id] = []
            scraping_status[task_id].update(status='completed', progress=100, message='No jobs found')
    except Exception as e:
        scraping_results[task_id] = []
        scraping_status[task_id].update(status='error', message=f'Error: {e}')
        print('Scraping error:', traceback.format_exc())

def _update_progress(task_id: str, percent: int, message: str):
    st = scraping_status.get(task_id)
    if st and st.get('status') == 'running':
        st['progress'] = min(max(int(percent), 0), 95)  # cap before finalization
        st['message'] = message

if __name__ == '__main__':
    app.run(debug=True, port=5000)
