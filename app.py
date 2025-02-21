from flask import Flask, render_template, request, jsonify
from SteamCsgo import SteamCsgo
import pandas as pd
import threading

app = Flask(__name__)
crawler_running = False
current_crawler = None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        global crawler_running, current_crawler
        price_range = int(request.form['price_range'])
        output_file = request.form['output_file']
        refresh_time = int(request.form['refresh_time'])
        
        # Start crawler in a separate thread
        current_crawler = SteamCsgo(price_range, output_file, refresh_time)
        crawler_thread = threading.Thread(target=current_crawler.get_page)
        crawler_thread.daemon = True
        crawler_thread.start()
        crawler_running = True
    
        return 'Data collection started!'
        
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    try:
        if current_crawler and current_crawler.save_file_path:
            df = pd.read_csv(current_crawler.save_file_path)
            return jsonify({
                'data': df.tail(10).to_dict('records'),  # Send last 10 rows
                'total_rows': len(df),
                'running': crawler_running
            })
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return jsonify({
            'data': [],
            'total_rows': 0,
            'running': crawler_running
        })

if __name__ == '__main__':
    app.run(debug=True)