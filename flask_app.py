import flask as fl
from flask_socketio import SocketIO, emit
import asyncio
from requests_html import AsyncHTMLSession
from bs4 import BeautifulSoup
from threading import Thread
import time
from websockets import client

app = fl.Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

class App:
    @staticmethod
    def get_text_by_id_ending(element, suffix):
        item = element.find(id=lambda x: x and x.endswith(suffix))
        return item.text if item else ''

    def __init__(self):
        self.priceboard_elements = []

    async def async_init(self):
        session = AsyncHTMLSession()
        resp = await session.get('https://priceboard.vcbs.com.vn/Priceboard')
        await resp.html.arender(sleep=2.5)
        self.priceboard_elements = resp.html.find('tbody > tr')

    async def data_loader(self):
        detail = []
        for element in self.priceboard_elements:
            try:
                row = BeautifulSoup(element.html, 'html.parser')
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
        return detail

async def load_data():
    app_instance = App()
    await app_instance.async_init()
    data = await app_instance.data_loader()
    return data

@app.route("/")
def home():
    return fl.render_template('home.html')

@app.route('/api/data')
def get_data():
    data = asyncio.run(load_data()) 
    return fl.jsonify(data)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def run_scraper():
    asyncio.set_event_loop(asyncio.new_event_loop()) 
    loop = asyncio.get_event_loop()
    while True:
        try:
            json_data = loop.run_until_complete(load_data())
            with app.app_context(): 
                socketio.emit('update_data', json_data)
            print(f"Data emitted {json_data}")
        except Exception as e:
            print(f"Error scraping: {e}")
        time.sleep(2)

if __name__ == '__main__':
    scraper_thread = Thread(target=run_scraper)
    scraper_thread.daemon = True  
    scraper_thread.start()

    socketio.run(app, debug=True)
