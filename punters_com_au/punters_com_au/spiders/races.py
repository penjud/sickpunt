"""Scraping of punters.com.au"""

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
            print(f"Extracted URL: {full_url}")
            urls.append(full_url)

        # Overview site
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_overview_page)


    def parse_overview_page(self, response):
        html_content = response.body
        df = extract_table_to_df(html_content)
        
        pattern = r'https:\/\/www\.punters\.com\.au\/form-guide\/(?P<place>[\w-]+)_(?P<id>\d+)'

        match = re.search(pattern, response.url)
        if match:
            place = match.group('place')
            id_ = match.group('id')
            print(f"place={place}")
            print(f"id={id_}")
        else:
            print("Pattern not found in the provided URL.")
        
        # Extract the title
        soup = BeautifulSoup(response.text, 'html.parser')
        race_name = soup.title.string

        print("=====================")
        print(f"URL: {response.url}")
        # print(df)
        for _, row in df.iterrows():
            horse_name = row['Horse Name']
            punters_com_au_collection.update_one({'Horse Name': horse_name}, {'$set': row.to_dict()}, upsert=True)

        print("=====================")
        
        # Assuming response.url and df are defined earlier
        match = re.search(r'_(\d+)/$', response.url)
        if match:
            possible_urls = []
            number = match.group(1)  # Extracted number
            possible_urls.append(f'https://www.punters.com.au/form-guide/spreadsheet-{number}')  # Formatted URL

            for i in range (3):
                date = (datetime.now()+timedelta(days=i)).strftime('%Y%m%d')
                possible_urls.append(f'https://www.punters.com.au/form-guide/spreadsheet-{date}-{place}-{number}')
            
            headers = {
                'User-Agent': 'Mozilla/5.0',
            }

            for url in possible_urls:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    csv_data = StringIO(response.text)
                    df2 = pd.read_csv(csv_data)
                    df2[df2.columns[1:]] = df2[df2.columns[:-1]].values
                    df_merged = pd.merge(df, df2, on='Horse Name')
                    print(df_merged.columns)
                    print(f'Total columns: {len(df_merged.columns)}')
                    df_merged = df_merged.fillna('NA')

                    for _, row in df_merged.iterrows():
                        horse_name = row['Horse Name']
                        punters_com_au_collection.update_one({'Horse Name': horse_name}, {'$set': row.to_dict()}, upsert=True)
                    
                    break  # Break the loop as we got a 200 status
                else:
                    print(f"Failed to download: {response.status_code}, trying next URL.")
                    for _, row in df.iterrows():
                        horse_name = row['Horse Name']
                        punters_com_au_collection.update_one({'Horse Name': horse_name}, {'$set': row.to_dict()}, upsert=True)
            

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


if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'FEEDS': {
            'items.json': {'format': 'json'},
        }
    })

    process.crawl(RacesSpider)
    process.start()
