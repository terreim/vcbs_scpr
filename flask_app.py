import flask as fl
import json
from flask_socketio import SocketIO
import asyncio
import vcbs_loader
# import time
from threading import Thread
import inspect

if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec

app = fl.Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def load_data():
    with open('data.json') as f:
        return json.load(f)

@app.route("/")
def home():
    return fl.render_template('home.html')

@app.route('/api/data')
def get_data():
    return fl.jsonify(load_data())

def run_scraper():
    
    while True:
        try:
            app = vcbs_loader.App()
            app.data_loader()
            json_data = load_data()
            socketio.emit('update_data', json_data)
        except Exception as e:
            print(f"Error scraping: {e}")
            # time.sleep(2.5)

def run_scraper_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_scraper())


if __name__ == '__main__':
    scraper_thread = Thread(target=run_scraper_thread)
    scraper_thread.start()
    
    socketio.run(app, debug=True)
