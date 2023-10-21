import logging
import re
import time
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
from scrapy import Request, Spider
from scrapy.crawler import CrawlerProcess

from betfair.config import punters_com_au_collection

log = logging.getLogger(__name__)

def reset_logging():
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    ch = logging.StreamHandler()
    ch.setLevel(logging.CRITICAL)
    root_logger.addHandler(ch)

def extract_table_to_df(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find("table", class_="form-guide-overview__table unresulted")
    rows = table.find_all("tr", class_="form-guide-overview__table-body")
    data = []
    for row in rows:
        horse_details_div = row.find("div", class_="form-guide-overview__horse")
        horse_name = horse_details_div.a.text.strip() if horse_details_div.a else ''
        cells = row.find_all("td")
        horse_number = cells[0].text.strip()
        last_10 = cells[2].text.strip()
        career = cells[3].text.strip()
        rtg = cells[4].text.strip()
        win_percent = cells[5].text.strip()
        placing_percent = cells[6].text.strip()
        avg_prize = cells[7].text.strip()
        wgt = cells[8].text.strip()
        bar = cells[9].text.strip()
        ppodds_span = cells[10].find('span', class_='ppodds')
        odds = ppodds_span.text.strip() if ppodds_span else 'N/A'
        data.append([horse_number, horse_name, last_10, career, rtg, win_percent, placing_percent, avg_prize, wgt, bar, odds])
    df = pd.DataFrame(data, columns=['Number', 'Horse Name', 'Last 10', 'Career', 'Rtg', 'W%', 'P%', 'Avg $', 'Wgt', 'Bar', 'Odds'])
    return df

class RacesSpider(Spider):
    name = 'races'
    allowed_domains = ['punters.com.au']

    def start_requests(self):
        url = 'https://www.punters.com.au/form-guide/'
        yield Request(url=url, callback=self.parse)

    def parse(self, response):
        urls = []
        for td in response.xpath('//td[@class="upcoming-race__td upcoming-race__event"]'):
            rel_url = td.xpath('.//a[@class="upcoming-race__event-link"]/@href').get()
            full_url = response.urljoin(rel_url)
            log.info(f"Extracted URL: {full_url}")
            urls.append(full_url)
        for url in urls:
            yield Request(response.urljoin(url), callback=self.parse_overview_page)

    def parse_overview_page(self, response):
        html_content = response.body
        df = extract_table_to_df(html_content)
        pattern_url = r'https:\/\/www\.punters\.com\.au\/form-guide\/(?P<place>[\w-]+)_(?P<id>\d+)'
        match_url = re.search(pattern_url, response.url)
        
        if match_url:
            id_ = match_url.group('id')
            place_basic = match_url.group('place')
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('title')
        
        if title_tag:
            title_text = title_tag.string
            match_title = re.search(r'([\w ]+R\d+)', title_text)
            if match_title:
                place = match_title.group(1).replace(' ', '-').lower()
        
        log.info("=====================")
        log.info(f"URL: {response.url}")
        
        file_url_rel = response.xpath('//a[re:test(@href, "/form-guide/spreadsheet-\d+/")]/@href').get()
        if file_url_rel:
            file_url = response.urljoin(file_url_rel)
            self.parse_csv_data(file_url, df)

    def parse_csv_data(self, file_url, df1):
        headers = {'User-Agent': 'Your User-Agent String', 'Referer': 'The Referer URL'}
        table_download_success = False
        response = requests.get(file_url, headers=headers)
        
        if response.status_code == 200:
            csv_data = StringIO(response.text)
            df2 = pd.read_csv(csv_data)
            table_download_success = True
            df2[df2.columns[1:]] = df2[df2.columns[:-1]].values
            df_merged = pd.merge(df1, df2, on='Horse Name')
            df_merged = df_merged.fillna('NA')
        
        if not table_download_success:
            log.warning(f'Failed to download table from URL: {file_url}')
            if response.status_code == 429:
                log.warning('Sleeping for 121 seconds')
                time.sleep(121)
            df_merged = df1
            
        df_merged['Horse Name'] = df_merged['Horse Name'].apply(lambda horse_name: re.sub("'", "", horse_name))
        df_merged['Horse Name'] = df_merged['Horse Name'].apply(lambda horse_name: re.sub("`", "", horse_name))
        
        log.info(f'Saving columns: {len(df_merged.columns)}')
        for _, row in df_merged.iterrows():
            horse_name = row['Horse Name']
            punters_com_au_collection.update_one({'Horse Name': horse_name}, {'$set': row.to_dict()}, upsert=True)

if __name__ == "__main__":
    reset_logging()
    logging.basicConfig(level=logging.CRITICAL)
    logging.getLogger('scrapy').propagate = False
    logging.getLogger('scrapy').setLevel(logging.ERROR)
    logging.getLogger('urllib3').propagate = False
    logging.getLogger('urllib3').setLevel(logging.ERROR)

    process = CrawlerProcess(settings={})
    process.crawl(RacesSpider)
    process.start()
