from typing import List
from threading import Thread, Timer
import urllib3
from urllib3.response import HTTPResponse
from lxml import html
import json
import re
from time import sleep
from datetime import  datetime
import logging
logging.basicConfig(level=logging.INFO)


RIGHTMOVE_URL = 'https://www.rightmove.co.uk/property-to-rent/find.html'

DJANGO_URL = 'http://huyg.site:8001/api/property/'


class RightmoveCrawler(Thread):
    http = None

    def __init__(self, name=None):
        Thread.__init__(self, name=name)
        self.http = urllib3.PoolManager()
    
    def run(self):
        logging.info("Crawler rightmove's first crawl after 60 seconds.")
        while True:
            sleep(60)
            try:
                self.crawl()
                break
            except Exception as e:
                e.with_traceback(e.__traceback__)
                logging.info("Crawler rightmove's first crawl failed. Trying...")
        logging.info("Crawler rightmove's first crawl succeed. Repeating...")
        self.repeat()
    
    def repeat(self):
        while True:
            sleep(3600*6)
            try:
                self.crawl()
            except Exception as e:
                e.with_traceback(e.__traceback__)
    
    def crawl(self):
        logging.info("Begin crawling")
        # self.http.request("DELETE", DJANGO_URL)
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
                sleep(1)
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
                            sleep(1)
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
        item_url = 'https://www.rightmove.co.uk' + item['propertyUrl']
        item_data = {
            'rightmove_id': item['id'],
            'title': item['displayAddress'],
            'type_name': item['propertySubType'],
            'distance': item['distance'],
            'beds': item['bedrooms'],
            'baths': item['bathrooms'] or 0,
            'url': item_url,
            'price_pcm': self.extract_price(item['price']['displayPrices'][0]['displayPrice']),
            'price_pw': self.extract_price(item['price']['displayPrices'][1]['displayPrice']),
            'available_date': '1970-01-01',
            'deposit': 0,
            'furnished': True
        }
        detail_page = self.http.request("GET", item_url).data.decode("utf-8", errors="replace")
        detail_tree: html.HtmlElement = html.fromstring(detail_page)
        detail_root: List[html.HtmlElement] = detail_tree.xpath("//h2[.='Letting details']/../dl")
        if len(detail_root) > 0:
            for di in detail_root[0].xpath("div"):
                if di is not None:
                    dt = di.xpath("dt")
                    dd = di.xpath("dd")
                    di_title: str = dt[0].text_content() if len(dt) > 0 else None
                    di_desc: str = dd[0].text_content() if len(dd) > 0 else None
                    if di_title is None:
                        continue
                    if di_title.startswith("Let available date"):
                        avaliable_date = datetime.strptime(di_desc, "%d/%m/%Y") if di_desc != "Now" else datetime.now()
                        item_data['available_date'] = avaliable_date.strftime("%Y-%m-%d") 
                    elif di_title.startswith("Furnish type"):
                        item_data['furnished'] = di_desc == "Furnished"
                    elif di_title.startswith("Deposit"):
                        item_data['deposit'] = self.extract_price(di_desc)
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
            logging.info("Update Property %s", rightmove_id)
            instance = check_result[0]
            instance_id = instance['id']
            save_res: HTTPResponse = self.http.request("PUT", f"{DJANGO_URL}{instance_id}/", body=item_body, headers=headers)
            if save_res.status == 400:
                logging.error(f"Property {rightmove_id} save failed.")
        else:
            save_res: HTTPResponse = self.http.request(method="POST", url=DJANGO_URL, body=item_body, headers=headers)
            if save_res.status == 400:
                logging.error(f"Property {rightmove_id} save failed.")


if __name__ == "__main__":
    logging.warning("crawler from main")
    crawler = RightmoveCrawler()
    crawler.run()
