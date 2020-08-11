import os
import time

import pandas as pd
import schedule
from dotenv import load_dotenv
from selenium import webdriver
from tqdm import tqdm

from parsers import CitimobilParser, WeatherParser, YandexTaxiParser

load_dotenv()

pick_up_address = os.getenv("PICK_UP_ADDRESS")
dest_address = os.getenv("DEST_ADDRESS")
weather_url = os.getenv("YANDEX_WEATHER_URL")

yandex = YandexTaxiParser(pick_up_address, dest_address)
citimobil = CitimobilParser(pick_up_address, dest_address)

options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options,
                          executable_path=("/home/sviperm/Documents"
                                           "/GitHub/taxi-price-watcher/"
                                           "files/chromedriver"))


def collect_data():
    result = []
    for parser in tqdm([yandex, citimobil]):
        try:
            result.extend(parser.get_price(driver))
        except Exception as e:
            print(e)

    try:
        print("Collecting weather...")
        weather = WeatherParser(weather_url).get_weather(driver)
        for r in result:
            r.update(weather)
    except Exception as e:
        print(e)

    if result:
        df = pd.read_csv('data.csv', header=0, index_col=0)
        df = df.append(result, ignore_index=True)
        df.to_csv('./data.csv')


schedule.every(5).minutes.do(collect_data)

while True:
    schedule.run_pending()
    time.sleep(1)
