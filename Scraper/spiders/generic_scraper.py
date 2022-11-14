import requests
import scrapy
import json
import dateutil.parser
from urllib.parse import urlparse

class BaseClass:
    
    def __init__(self, config):
        self.seed_url = config['url']
        self.payload_data = config['payload_data']
        self.selectors = config['selector']
        self.request_header = config['request_headers']
        self.page_no = 0
        self.doc_urls = []
        self.final_data = []
        self.next_page = True
        self.config_file = {}
    
    def get_date(self, s_date): 
        if s_date:
            return str(dateutil.parser.parse(s_date)).split(' ',1)[0]
        else:
            return None

    def domain_validator(self, url):
        domain_validated = False
        for ext in ['.asp', '.aspx']:
            if ext in url:
                domain_validated = True
        return domain_validated
    
    def extract_domain(self, s_url):
        domain = urlparse(s_url).netloc
        return domain

    def set_url(self):
        return self.seed_url

    def make_request(self, method, headers={}, payload={}, proxy={}):
        url = self.set_url()
        html_response = requests.request(method, url, headers=headers, data=payload, proxies=proxy)
        response = scrapy.Selector(html_response)
        domain = self.extract_domain(html_response.url)
        return html_response, response, domain

    def write_content(self, text):
        with open('output.json', 'w') as f:
            json.dump(text, f)
    
    def extract_article(self, results, domain):
        for result in results:
            article_title = result.xpath(f'.{self.selectors["article_title"]}').get()
            article_type = result.xpath(f'.{self.selectors["document_type"]}').get()
            doc_url = result.xpath(f'.{self.selectors["article_link"]}').get()
            if doc_url:
                doc_url = f'https://{domain}' + doc_url
            article_date = self.get_date(result.xpath(f'.{self.selectors["article_date"]}').get())
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
                self.next_page = False
                self.write_content(self.final_data)
                break
    
    def extract_data(self):
        html_response, response, domain = self.make_request(method="GET", headers=self.request_header)
        domain_validated = self.domain_validator(html_response.url)
        event_target = self.payload_data["EVENT_TARGET"]
        while self.next_page and domain_validated:
            event_validation = response.xpath(self.payload_data["EVENT_VALIDATOR"]).get()
            view_state = response.xpath(self.payload_data["VIEW_STATE"]).get()
            payload = {
                '__EVENTTARGET': event_target.format(self.page_no) if '{:02}' in event_target else event_target,
                '__VIEWSTATE': view_state,
                '__EVENTVALIDATION': event_validation
            }
            self.page_no += 1
            html_response, response, domain = self.make_request(method="POST", payload=payload, headers=self.request_header)
            results = response.xpath(self.selectors["root_xpath"])
            if results:
                self.extract_article(results, domain)
            else:
                break