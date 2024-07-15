import gevent.monkey
gevent.monkey.patch_all()

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import gevent
import json
import asyncio
from threading import Event, Lock

app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*", websocket=True, logger=True, engineio_logger=True)
app.config['SECRET_KEY'] = 'top-secret!'
PRICEBOARD_URL = 'https://priceboard.vcbs.com.vn/Priceboard'
JSON_DATA_FILE = 'data.json'

client_connected = Event()
thread = None
thread_lock = Lock()
scraper = None

# Scraper and necessities
class Scrape_Driver:
    @staticmethod
    def get_element(element, suffix):
        item = element.find('td', id=lambda x: x and x.endswith(suffix))
        if item:
            price = item.text.strip()
            if price:
                try:
                    return price
                except ValueError:
                    return price
        return None
    
    @staticmethod
    def initialize_session():
        session = HTMLSession()
        # print('Initialized session!')
        # socketio.emit('log_response', {'data': 'initialized session!'})
        return session

    def __init__(self):
        self.priceboard_elements = []
        self.stock_names = []
        self.row_element = []
        self.session = self.initialize_session()
        # print('Scrape_Driver initialized!')

    def scrape_elements(self):
        # print('Scraping elements...')
        # socketio.emit('log_response', {'data': 'scraping elements...'})
        try:
            self.stock_names = []
            self.row_element = []
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response = self.session.get(PRICEBOARD_URL)
            response.html.render(sleep=3.5)
            soup = BeautifulSoup(response.html.html, 'html.parser')
            self.priceboard_elements = soup.select('#priceboardContentTableBody > tr')
            # print('Scraped elements!')

            for element in self.priceboard_elements:
                try:
                    row = BeautifulSoup(str(element), 'html.parser')
                    name = row.find('span', class_='symbol_link').text
                    if 's_8_s' in name:
                        continue
                    self.stock_names.append(name)
                    self.row_element.append(row)
                except AttributeError:
                    pass
            # socketio.emit('log_response', {'data': 'scraped elements!'})
        except Exception as e:
            print(f'Error in scrape_elements: {e}')
            socketio.emit('log_response', {'data': f'error in scrape_elements: {e}'})

    def extracted_elements(self):
        # print('Extracting elements...')
        # socketio.emit('log_response', {'data': 'extracting elements...'})
        detail = []
        for name, row in zip(self.stock_names, self.row_element):
            try:
                row_data = {
                    'name': name,
                    'ceiling': self.get_element(row, 'ceiling'),
                    'floor': self.get_element(row, 'floor'),
                    'prior_close_price': self.get_element(row, 'priorClosePrice'),
                    'change': self.get_element(row, 'change'),
                    'close_price': self.get_element(row, 'closePrice'),
                    'close_volume': self.get_element(row, 'closeVolume'),
                    'total_trading': self.get_element(row, 'totalTrading'),
                    'open': self.get_element(row, 'open'),
                    'high': self.get_element(row, 'high'),
                    'low': self.get_element(row, 'low'),
                    'foreign_buy': self.get_element(row, 'foreignBuy'),
                    'foreign_sell': self.get_element(row, 'foreignSell'),
                    'foreign_remain': self.get_element(row, 'foreignRemain')
                }
                detail.append(row_data)
            except AttributeError as e:
                print(f'Error parsing element: {e}')
                socketio.emit('log_response', {'data': f'error parsing element: {e}'})
                continue

        try:
            with open(JSON_DATA_FILE, 'w') as file:
                json.dump(detail, file)
            # print('Extracted elements!')
            # socketio.emit('log_response', {'data': 'extracted elements!'})
        except Exception as e:
            print(f'Error writing to file: {e}')
            socketio.emit('log_response', {'data': f'error writing to file: {e}'})
        return detail
        
    def close_session(self):
        # print('Session closed!')
        socketio.emit('log_response', {'data': 'session closed!'})
        self.session.close()

# Flask and Websocket
@app.route("/")
def home():
    return render_template('home.html')

@app.route(f'/api/data')
def get_data():
    data = load_data()
    return jsonify(data)

@app.route('/api/data/custom')
def get_data_custom():
    data = update_and_get_data()
    selected_stocks = request.args.getlist('stock_name')
    selected_columns = request.args.getlist('columns')

    if not selected_stocks and not selected_columns:
        return jsonify(data)

    filtered_data = []

    for stock in data:
        if stock['name'] in selected_stocks:
            filtered_stock = {key: value for key, value in stock.items() if key in selected_columns or key == 'name'}
            filtered_data.append(filtered_stock)

    return jsonify(filtered_data)

@socketio.on('connect')
def on_connect():
    global thread, scraper
    print('Client connected')
    if not scraper:
        scraper = Scrape_Driver()
    with thread_lock:
        if thread is None:
            client_connected.set()
            thread = socketio.start_background_task(run_app, client_connected, scraper)
    socketio.emit('log_response', {'data': 'client connected!'})

@socketio.on('disconnect')
def on_disconnect():
    global thread, scraper
    print('Client disconnected')
    client_connected.clear()
    with thread_lock:
        if thread is not None:
            thread.join()
            thread = None
    if scraper:
        scraper.close_session()
        scraper = None
    print('Background task stopped.')

@socketio.on('hello_event')
def handle_my_event(data):
    print('Received hello_event:', data)
    # socketio.emit('log_response', {'data': 'test response from server!'})

# Initialization
def update_and_get_data():
    global scraper
    if scraper is None:
        scraper = Scrape_Driver()
    update_data(scraper)
    return load_data()

def load_data():
    # print('Loading data from JSON file.')
    # socketio.emit('log_response', {'data': 'loading data from JSON file!'})
    try:
        with open(JSON_DATA_FILE) as f:
            data = json.load(f)
        # print('Data loaded successfully.')
        # socketio.emit('log_response', {'data': 'data loaded successfully!'})
        return data
    except FileNotFoundError:
        print('Data file not found.')
        socketio.emit('log_response', {'data': 'data file not found!'})
        return []

def update_data(scraper):
    # print('Updating data...')
    # socketio.emit('log_response', {'data': 'updating data...'})
    last_data = load_data()
    scraper.scrape_elements()
    current_data = scraper.extracted_elements()
    if current_data != last_data:
        socketio.emit('update_data', current_data)
    else:
        socketio.emit('log_response', {'data': 'no new data to update.'})

def run_app(event, scraper):
    # print('Running app...')
    # socketio.emit('log_response', {'data': 'running app...'})
    try:
        while event.is_set():
            update_data(scraper)
            socketio.sleep(3)  # Wait for 3 seconds before the next update
    finally:
        event.clear()
        print('Background task stopped.')

if __name__ == '__main__':
    # socketio.emit('log_response', {'data': 'scrape_Driver initialized!'})
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
