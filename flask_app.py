import flask as fl
import json
from flask_socketio import SocketIO
import asyncio
import vcbs_loader
import eventlet
# import time
from threading import Thread
import inspect

eventlet.monkey_patch()

app = fl.Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

def load_data():
    with open('data.json') as f:
        return json.load(f)
    # app = vcbs_loader.App()
    # data = app.data_loader()
    # return data

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
            check_ = app.data_loader()
            print(f"Loading {check_}") 
            json_data = load_data()
            socketio.emit('update_data', json_data)
            print(f"Data emitted {json_data}")
        except Exception as e:
            print(f"Error scraping: {e}")
            # time.sleep(2.5)

if __name__ == '__main__':
    scraper_thread = Thread(target=run_scraper)
    scraper_thread.start()
    
    socketio.run(app, debug=True)
