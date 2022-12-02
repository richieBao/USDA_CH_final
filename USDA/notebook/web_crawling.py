# -*- coding: utf-8 -*-
"""
Created on Sat Nov 26 20:38:53 2022

@author: richie bao
"""
import logging
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)

class Crawler:

    def __init__(self, urls=[],iter=True):
        self.visited_urls = []
        self.urls_to_visit = urls
        self.iter=iter
        self.visited_urls_dict={}

    def download_url(self, url):
        return requests.get(url).text

    def get_linked_urls(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        # print("-"*50)
        for link in soup.find_all('a'):
            path = link.get('href')
            # print(path)
            if path and path.startswith('/'):
                path = urljoin(url, path)
            yield path

    def add_url_to_visit(self, url):
        if url not in self.visited_urls and url not in self.urls_to_visit:
            self.urls_to_visit.append(url)

    def crawl(self, url_):
        self.visited_urls_dict[url_]=[]
        html = self.download_url(url_)
        # print(html)
        for url in self.get_linked_urls(url_, html):
            # print(url)
            if self.iter:
                self.add_url_to_visit(url)
            else:
                self.visited_urls_dict[url_].append(url)

    def run(self):
        while self.urls_to_visit:
            url = self.urls_to_visit.pop(0)
            logging.info(f'Crawling: {url}')
            
            try:
                self.crawl(url)
            except Exception:
                logging.exception(f'Failed to crawl: {url}')
            finally:
                self.visited_urls.append(url)
        
                
if __name__=="__main__":
    url_root_lst=[f'https://e4ftl01.cr.usgs.gov/MOTA/MCD12Q1.006/{i}.01.01/' for i in range(2001,2021,1)]   
    wc=Crawler(urls=url_root_lst,iter=False)
    wc.run() 
    print(wc.visited_urls_dict)

    