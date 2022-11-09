import requests
import scrapy
import json
import dateutil.parser
from urllib.parse import urlparse

class BaseClass:
    
    def __init__(self, config):
        self.seed_url = config['url']
        self.event_validation = config['payload_data']['EVENT_VALIDATOR']
        self.view_state = config['payload_data']['VIEW_STATE']
        self.event_target = config['payload_data']['EVENT_TARGET']
        self.root_path = config['root_xpath']
        self.article_title = config['article_title']
        self.doc_type = config['document_type']
        self.article_link = config['article_link']
        self.article_date = config['article_date']
        self.request_header = config['request_headers']
        self.page_no = 0
        self.doc_urls = []
        self.final_data = []
        self.next_flag = True
        self.config_file = {}
    
    def get_date(self, s_date):
        if s_date:
            return str(dateutil.parser.parse(s_date)).split(' ',1)[0]
        else:
            return None
    
    def extract_domain(self, s_url):
        domain = urlparse(s_url).netloc
        return domain

    def set_url(self):
        return self.seed_url

    def get_request(self, headers={}, proxy={}):
        url = self.set_url()
        response = scrapy.Selector(requests.request("GET", url, headers=headers, proxies=proxy))
        return response

    def post_request(self, headers={}, payload={}, proxy={}):
        url = self.set_url()
        html_response = requests.request("POST", url, headers=headers, data=payload, proxies=proxy)
        response = scrapy.Selector(html_response)
        domain = self.extract_domain(html_response.url)
        return response, domain
    
    def write_content(self, text):
        with open('output.json', 'w') as f:
            json.dump(text, f)
    
    def extract_data(self):
        response = self.get_request(headers=self.request_header)
        event_target = self.event_target
        while self.next_flag:
            event_validation = response.xpath(self.event_validation).get()
            view_state = response.xpath(self.view_state).get()
            payload = {
                '__EVENTTARGET': event_target.format(self.page_no) if '{:02}' in event_target else event_target,
                '__VIEWSTATE': view_state,
                '__EVENTVALIDATION': event_validation
            }
            self.page_no += 1
            print(self.page_no)
            response, domain = self.post_request(payload=payload, headers=self.request_header)
            results = response.xpath(self.root_path)
            if not results:
                break
            for result in results:
                article_title = result.xpath(f'.{self.article_title}').get()
                article_type = result.xpath(f'.{self.doc_type}').get()
                doc_url = result.xpath(f'.{self.article_link}').get()
                if doc_url:
                    doc_url = f'https://{domain}' + doc_url
                article_date = self.get_date(result.xpath(f'.{self.article_date}').get())
                if doc_url not in self.doc_urls:
                    self.doc_urls.append(doc_url)
                    data_dict = {
                        'article_title': article_title,
                        'article_type': article_type,
                        'article_pdf_link': doc_url,
                        'article_date': article_date
                    }
                    self.final_data.append(data_dict)
                else:
                    self.next_flag = False
                    self.write_content(self.final_data)
                    break