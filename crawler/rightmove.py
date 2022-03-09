from threading import Thread
import urllib3
from urllib3.response import HTTPResponse
from lxml import html
import json
import re
from time import sleep
import logging
logging.basicConfig(level=logging.INFO)


RIGHTMOVE_URL = 'https://www.rightmove.co.uk/property-to-rent/find.html'

DJANGO_URL = 'http://localhost:8000/api/property/'


class RightmoveCrawler(Thread):
    http = None

    def __init__(self, name=None):
        Thread.__init__(self, name=name)
        self.http = urllib3.PoolManager()
    
    def run(self):
        property_type_list = [
            ('houses', 'detached,semi-detached,terraced'),
            ('flats', 'flat')
        ]
        for property_type in property_type_list:
            sleep(1)
            self.list_by_type(property_type)
    
    def list_by_type(self, property_type):
        page_first = self.get_page(1, property_type)
        if page_first is not None:
            for item in page_first['properties']:
                logging.info('Property %s, %s', item['id'], property_type[0])
                self.save_item(item)
            pn_total = int(page_first['pagination']['total'])
            pn_now = int(page_first['pagination']['page'])
            if pn_total > 1:
                while pn_now < pn_total:
                    sleep(1)
                    pn_now = pn_now + 1
                    page_now = self.get_page(pn_now, property_type)
                    if page_now is not None:
                        for item in page_now['properties']:
                            logging.info('Property %s, %s', item['id'], property_type[0])
                            self.save_item(item)
        else:
            logging.error('Cannot find first page.')
    

    def get_page(self, page_number, property_type):
        query = {
            'locationIdentifier': 'POSTCODE^104917',
            'maxBedrooms': 4,
            'minBedrooms': 4,
            'maxPrice': 3000,
            'minPrice': 600,
            'radius': 5.0,
            'propertyTypes': property_type[1],
            'primaryDisplayPropertyType': property_type[0],
            'includeLetAgreed': 'false',
            'numberOfPropertiesPerPage': 24,
            'index': (page_number - 1) * 24,
            'viewType': 'LIST',
            'channel': 'RENT',
            'areaSizeUnit': 'sqft',
            'currencyCode': 'GBP',
            'isFetching': 'false'
        }
        list_page = self.http.request("GET", RIGHTMOVE_URL, fields=query).data
        list_data = list_page.decode("utf-8", errors="replace")
        return self.parse_page(list_data)
    
    def parse_page(self, page: str):
        root = html.fromstring(page)
        script_list = [x.text for x in root.xpath("//script") if x is not None]
        data = None
        for script in script_list:
            if script is not None and script.startswith("window.jsonModel ="):
                data_text = script.split(" = ", 1)[1]
                data = json.loads(data_text)
                break
        else:
            logging.error("Avaliable Script Not Found!")

        return data
    
    def extract_price(self, display_price):
        if (match := re.search('\d+(\,\d+)?', display_price)) is not None:
            price_text = match.group(0)
            price = re.sub('\,', '', price_text)
            return int(price)
        else:
            return 0
    
    def save_item(self, item):
        item_data = {
            'rightmove_id': item['id'],
            'title': item['displayAddress'],
            'type_name': item['propertySubType'],
            'distance': item['distance'],
            'beds': item['bedrooms'],
            'baths': item['bathrooms'] or 0,
            'url': 'https://www.rightmove.co.uk/' + item['propertyUrl'],
            'price_pcm': self.extract_price(item['price']['displayPrices'][0]['displayPrice']),
            'price_pw': self.extract_price(item['price']['displayPrices'][1]['displayPrice']),
            'available_date': '1970-01-01',
            'deposit': 0,
        }
        item_body = json.dumps(item_data).encode('utf-8')
        headers = {
            "Content-Type": "application/json"
        }
        rightmove_id = item['id']
        check_res: HTTPResponse = self.http.request("GET", DJANGO_URL, fields={
            'rightmove_id': rightmove_id
        })
        check_result: list = json.loads(check_res.data.decode("utf-8"))
        if len(check_result) > 0:
            instance = check_result[0]
            instance_id = instance['id']
            save_res: HTTPResponse = self.http.request("PUT", f"{DJANGO_URL}{instance_id}/", body=item_body, headers=headers)
            if save_res.status == 400:
                logging.error(f"Property {rightmove_id} save failed.")
        else:
            save_res: HTTPResponse = self.http.request(method="POST", url=DJANGO_URL, body=item_body, headers=headers)
            if save_res.status == 400:
                logging.error(f"Property {rightmove_id} save failed.")


if __name__=="__main__":
    crawler = RightmoveCrawler()
    crawler.run()
