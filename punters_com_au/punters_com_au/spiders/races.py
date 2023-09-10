from pathlib import Path

import scrapy
import pandas as pd
from bs4 import BeautifulSoup
import re

class RacesSpider(scrapy.Spider):
    name = 'races'
    allowed_domains = ['punters.com.au']

    def start_requests(self):
        url = 'http://www.punters.com.au/'
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        urls = response.xpath(
            "//div[@class='next-to-jump-horizontal__main punters-generic-component__main']/a/@href").extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_next_page)

    def parse_next_page(self, response):
        html_content = response.body
        df = extract_table_to_df(html_content)
        # For demonstration purposes, print the first 5 rows
        
        pattern = r'https:\/\/www\.punters\.com\.au\/form-guide\/(?P<place>[\w-]+)_(?P<id>\d+)'

        match = re.search(pattern, response.url)
        if match:
            place = match.group('place')
            id_ = match.group('id')
            print(f"place={place}")
            print(f"id={id_}")
        else:
            print("Pattern not found in the provided URL.")
        
        print ("=====================")
        print(f"URL: {response.url}")
        print(df)
        print ("=====================")


def extract_table_to_df(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find("table", class_="form-guide-overview__table unresulted")

    rows = table.find_all("tr", class_="form-guide-overview__table-body")

    data = []
    for row in rows:
        horse_details_div = row.find(
            "div", class_="form-guide-overview__horse")
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


        data.append([horse_number, horse_name, last_10, career, rtg,
                    win_percent, placing_percent, avg_prize, wgt, bar, odds])

    # Convert the list to a pandas DataFrame
    df = pd.DataFrame(data, columns=['Number', 'Horse Name', 'Last 10',
                      'Career', 'Rtg', 'W%', 'P%', 'Avg $', 'Wgt', 'Bar', 'Odds'])

    return df