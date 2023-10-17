"""Scraping of punters.com.au"""

import logging
import re
from pathlib import Path

import pandas as pd
import scrapy
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
from betfair.config import punters_com_au_collection
import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
from betfair.helper import init_logger

log=logging.getLogger(__name__)


class RacesSpider(scrapy.Spider):
    name = 'races'
    allowed_domains = ['punters.com.au']

    def start_requests(self):
        url = 'https://www.punters.com.au/form-guide/'
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        urls = []
        for td in response.xpath('//td[@class="upcoming-race__td upcoming-race__event"]'):
            # Extract the href attribute of the <a> tag using XPath
            rel_url = td.xpath('.//a[@class="upcoming-race__event-link"]/@href').get()
            # Construct the full URL
            full_url = response.urljoin(rel_url)
            
            # Output or further process the extracted URL
            log.info(f"Extracted URL: {full_url}")
            urls.append(full_url)

        # Overview site
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_overview_page)


    def parse_overview_page(self, response):
        html_content = response.body
        df = extract_table_to_df(html_content)
        
        # Extract id_ from the URL
        pattern_url = r'https:\/\/www\.punters\.com\.au\/form-guide\/(?P<place>[\w-]+)_(?P<id>\d+)'
        match_url = re.search(pattern_url, response.url)
        if match_url:
            id_ = match_url.group('id')
            place_basic = match_url.group('place')

        # Extract title from the parsed HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.string
            # Use regex to match the first part of the title and convert it to the required format
            match_title = re.search(r'([\w ]+R\d+)', title_text)
            if match_title:
                place = match_title.group(1).replace(' ', '-').lower()
            else:
                log.warning(f'Failed to extract place from title: {title_text}')



        # Extract the title
        soup = BeautifulSoup(response.text, 'html.parser')
        race_name = soup.title.string

        log.info("=====================")
        log.info(f"URL: {response.url}")
        

        file_url = ['https:\/\/www\.punters\.com\.au\/']

        file_url_rel = response.xpath('//a[re:test(@href, "/form-guide/spreadsheet-\d+/")]/@href').get()
        if file_url_rel:  # To ensure the element was found
            file_url = response.urljoin(file_url_rel)
            scrapy.Request(file_url, callback=self.parse_csv)
            headers = {
                'User-Agent': 'Your User-Agent String',
                'Referer': 'The Referer URL',
                # Add other headers if necessary
            }
            table_download_succes=False
            response = requests.get(file_url, headers=headers)
            if response.status_code == 200:
                csv_data = StringIO(response.text)
                df2 = pd.read_csv(csv_data)
                table_download_succes = True
                df2[df2.columns[1:]] = df2[df2.columns[:-1]].values
                df_merged = pd.merge(df, df2, on='Horse Name')
                df_merged = df_merged.fillna('NA')
                     
            if not table_download_succes:
                log.warning(f'Failed to download table from URLs: {file_url}')
                df_merged=df
            
            # save data
            log.info(f'Saving columns: {len(df_merged.columns)}')
            for _, row in df_merged.iterrows():
                horse_name = row['Horse Name']
                punters_com_au_collection.update_one({'Horse Name': horse_name}, {'$set': row.to_dict()}, upsert=True)
        
    def parse_csv(self, response):
        # Reading CSV directly into Pandas DataFrame from response.body
        csv_content = StringIO(response.text)
        df = pd.read_csv(csv_content)
        
def extract_table_to_df(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find("table", class_="form-guide-overview__table unresulted")

    rows = table.find_all("tr", class_="form-guide-overview__table-body")

    data = []
    for row in rows:
        horse_details_div = row.find(
            "div", class_="form-guide-overview__horse")
        horse_name = horse_details_div.a.text.strip() if horse_details_div.a else ''
        horse_name = re.sub("'", "", horse_name)
        horse_name = re.sub("""`""", "", horse_name)
        
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

        data.append([horse_number, horse_name, last_10, career, rtg,
                    win_percent, placing_percent, avg_prize, wgt, bar, odds])

    # Convert the list to a pandas DataFrame
    df = pd.DataFrame(data, columns=['Number', 'Horse Name', 'Last 10',
                      'Career', 'Rtg', 'W%', 'P%', 'Avg $', 'Wgt', 'Bar', 'Odds'])

    return df
def reset_logging():
    # Get the root logger
    root_logger = logging.getLogger()
    # Remove all existing handlers from the root logger
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    # Add a new handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.CRITICAL)
    root_logger.addHandler(ch)

if __name__ == "__main__":

    process = CrawlerProcess(settings={})
    reset_logging()
    logging.basicConfig(level=logging.CRITICAL)
    logging.getLogger('scrapy').propagate = False
    logging.getLogger('scrapy').setLevel(logging.ERROR)
    logging.getLogger('urllib3').propagate = False
    logging.getLogger('urllib3').setLevel(logging.ERROR)  

    process.crawl(RacesSpider)
    process.start()
