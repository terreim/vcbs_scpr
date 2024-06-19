from flask import Flask, render_template, jsonify, session
from flask_session import Session
from flask_socketio import SocketIO, emit
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import threading
import json
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'
app.config['SESSION_TYPE'] = 'filesystem'
PRICEBOARD_URL = 'https://priceboard.vcbs.com.vn/Priceboard'
JSON_DATA_FILE = 'data.json'
Session(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class VCBS_Scraper:
    @staticmethod
    def get_text_by_id_ending(element, suffix):
        item = element.find(id=lambda x: x and x.endswith(suffix))
        return item.text if item else ''
    
    @staticmethod
    def initialize_driver():
        options = Options()
        options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)

    def __init__(self):
        self.priceboard_elements = []
        self.driver = self.initialize_driver()  
        self.lock = threading.Lock()

    def scrape_data(self):
        self.driver.get(PRICEBOARD_URL)
        time.sleep(2.5)
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        self.priceboard_elements = soup.select('tbody > tr')

    def data_loader(self):
        detail = []
        for element in self.priceboard_elements:
            try:
                row = BeautifulSoup(str(element), 'html.parser')
                name = row.find('span', class_='symbol_link').text
                if 's_8_s' in name:
                    continue

                row_data = {
                    'name': name,
                    'ceiling': self.get_text_by_id_ending(row, 'ceiling'),
                    'floor': self.get_text_by_id_ending(row, 'floor'),
                    'prior_close_price': self.get_text_by_id_ending(row, 'priorClosePrice'),
                    'p3_best_bid': self.get_text_by_id_ending(row, 'best3Bid'),
                    'p3_best_bid_vol': self.get_text_by_id_ending(row, 'best3BidVolume'),
                    'p2_best_bid': self.get_text_by_id_ending(row, 'best2Bid'),
                    'p2_best_bid_vol': self.get_text_by_id_ending(row, 'best2BidVolume'),
                    'p1_best_bid': self.get_text_by_id_ending(row, 'best1Bid'),
                    'p1_best_bid_vol': self.get_text_by_id_ending(row, 'best1BidVolume'),
                    'change': self.get_text_by_id_ending(row, 'change'),
                    'close_price': self.get_text_by_id_ending(row, 'closePrice'),
                    'close_volume': self.get_text_by_id_ending(row, 'closeVolume'),
                    'p1_best_ask': self.get_text_by_id_ending(row, 'best1Offer'),
                    'p1_best_ask_vol': self.get_text_by_id_ending(row, 'best1OfferVolume'),
                    'p2_best_ask': self.get_text_by_id_ending(row, 'best2Offer'),
                    'p2_best_ask_vol': self.get_text_by_id_ending(row, 'best2OfferVolume'),
                    'p3_best_ask': self.get_text_by_id_ending(row, 'best3Offer'),
                    'p3_best_ask_vol': self.get_text_by_id_ending(row, 'best3OfferVolume'),
                    'total_trading': self.get_text_by_id_ending(row, 'totalTrading'),
                    'open': self.get_text_by_id_ending(row, 'open'),
                    'high': self.get_text_by_id_ending(row, 'high'),
                    'low': self.get_text_by_id_ending(row, 'low'),
                    'foreign_buy': self.get_text_by_id_ending(row, 'foreignBuy'),
                    'foreign_sell': self.get_text_by_id_ending(row, 'foreignSell'),
                    'foreign_remain': self.get_text_by_id_ending(row, 'foreignRemain')
                }
                detail.append(row_data)

            except AttributeError:
                continue

        with open(JSON_DATA_FILE, 'w') as file:
            json.dump(detail, file)
        
    def close_driver(self):
        self.driver.quit()

def load_data():
    with open(JSON_DATA_FILE) as f:
        return json.load(f)

def initialize_data(scraper):
    scraper.scrape_data()
    scraper.data_loader()
    with open('data.json') as f:
        data = json.load(f)
    return data

def run_scraper(scraper):
    while True:
        try:
            json_data = initialize_data(scraper)
            with app.app_context():
                socketio.emit('update_data', json_data)
            time.sleep(3)  
        except Exception as e:
            print(f"Error scraping: {e}")
            time.sleep(3)

@app.route("/")
def home():
    return render_template('home.html')

@app.route('/api/data')
def get_data():
    with open(JSON_DATA_FILE) as f:
        data = json.load(f)
    return jsonify(data)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    scraper_thread = threading.Thread(target=run_scraper, args=(scraper,))
    scraper_thread.daemon = True
    scraper_thread.start()

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    scraper = VCBS_Scraper()
    socketio.run(app, debug=True)
    scraper.close_driver()
