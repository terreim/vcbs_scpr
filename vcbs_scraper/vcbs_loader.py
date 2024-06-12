from requests_html import HTMLSession
from bs4 import BeautifulSoup
import json

class App():
    @staticmethod
    def get_text_by_id_ending(element, suffix):
        item = element.find(id=lambda x: x and x.endswith(suffix))
        return item.text if item else ''

    def __init__(self):
        session = HTMLSession()
        resp = session.get('https://priceboard.vcbs.com.vn/Priceboard')
        resp.html.render(sleep=3)
        self.priceboard_elements = resp.html.find('tbody > tr')
    
    def data_loader(self):
        self.detail_ = []
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
                self.detail_.append(row_data)

            except AttributeError:
                continue

        with open('data.json', 'w') as file:
            json.dump(self.detail_, file)
