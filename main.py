import os
import re
import time
from itertools import permutations, product

import pandas as pd
import schedule
from dotenv import load_dotenv
from selenium import webdriver
from tqdm import tqdm

from parsers import CitimobilParser, WeatherParser, YandexTaxiParser

# .env variables
load_dotenv()

PICK_UP_ADDRESS = os.getenv("PICK_UP_ADDRESS")
DEST_ADDRESS = os.getenv("DEST_ADDRESS")
YANDEX_WEATHER_URL = os.getenv("YANDEX_WEATHER_URL")
MODE = os.getenv("MODE")

# Addresses
pick_up_addresses = list(filter(None, re.split(r";\s*", PICK_UP_ADDRESS)))
dest_addresses = list(filter(None, re.split(r";\s*", DEST_ADDRESS)))

# Create combinations of addresses
addresses = []
if MODE == "PAIRS":
    for i in range(len(pick_up_addresses)):
        permut = list(permutations((pick_up_addresses[i], dest_addresses[i])))
        addresses.extend(permut)

elif MODE == "PRODUCT":
    addresses = list(product(pick_up_addresses, dest_addresses))
    addresses.extend(list(product(dest_addresses, pick_up_addresses)))

# Create parsers
parsers = []
for parser in (YandexTaxiParser, CitimobilParser):
    for adr in addresses:
        parsers.append(parser(*adr))

# Chrome options
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")


def collect_data(debug=False):
    """Parse and collect taxi, weather data from web

    Args:
        debug (bool, optional): If debug is True, dont write data in data.csv. 
        Defaults to False.

    Returns:
        Returns only if debag=True
        list: list of dictionares
    """
    driver = webdriver.Chrome(options=options,
                              executable_path=("./files/chromedriver"))
    result = []
    for parser in tqdm(parsers):
        try:
            result.extend(parser.get_price(driver))
        except Exception as e:
            print(parser)
            print(e)

    try:
        print("Collecting weather...")
        weather = WeatherParser(YANDEX_WEATHER_URL).get_weather(driver)
        for r in result:
            r.update(weather)
    except Exception as e:
        print(e)

    driver.quit()

    if result:
        if debug:
            return result
        else:
            file = 'data.csv'
            df = pd.read_csv(file, header=0, index_col=0)
            df = df.append(result, ignore_index=True)
            df.to_csv(f"./{file}")
            print(f"Saved to {file}")
    else:
        print("No result")
        if debug:
            return []


schedule.every(5).minutes.do(collect_data)

while True:
    schedule.run_pending()
    time.sleep(1)
