import re
import time
from abc import abstractmethod

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TaxiParser:
    def __init__(self,
                 taxi_name,
                 pick_up_address,
                 arrival_address,
                 tariff_name_class_name,
                 tariff_price_class_name):
        self.taxi_name = taxi_name
        self.pick_up_address = pick_up_address
        self.arrival_address = arrival_address
        self._tariff_name_class_name = tariff_name_class_name
        self._tariff_price_class_name = tariff_price_class_name
        self._tariffs = None

    @abstractmethod
    def parse(self, driver):
        pass

    def get_price(self, driver):
        self.parse(driver)

        result = []
        for t in self._tariffs:
            name = t.find_element_by_class_name(self._tariff_name_class_name).text
            price = t.find_element_by_class_name(self._tariff_price_class_name).text
            price = re.search(r"^\d+", price).group(0)
            result.append({
                "name": name,
                "pick_up_address": self.pick_up_address,
                "arrival_address": self.arrival_address,
                "price": price,
                "taxi": self.taxi_name,
                "date": time.strftime("%d.%m.%Y", time.localtime()),
                "time": time.strftime("%H:%M", time.localtime()),
            })
        return result


class YandexTaxiParser(TaxiParser):
    def __init__(self, pick_up_address, arrival_address):
        super().__init__('yandex',
                         pick_up_address,
                         arrival_address,
                         'TariffCard__name',
                         'TariffCard__price')

    def parse(self, driver):
        driver.get("https://taxi.yandex.ru/")

        pick_up = driver.find_element_by_css_selector("[placeholder='Адрес места отправления']")
        pick_up.send_keys(self.pick_up_address)
        time.sleep(1)

        pick_up.send_keys(Keys.ARROW_DOWN)
        pick_up.send_keys(Keys.ENTER)
        time.sleep(1)

        dest = driver.find_element_by_css_selector("[placeholder='Адрес места назначения']")
        dest.send_keys(self.arrival_address)
        time.sleep(1)

        dest.send_keys(Keys.ARROW_DOWN)
        dest.send_keys(Keys.ENTER)
        time.sleep(1)

        self._tariffs = driver.find_elements_by_class_name('TariffCard')


class CitimobilParser(TaxiParser):
    def __init__(self, pick_up_address, arrival_address):
        super().__init__('citimobil',
                         pick_up_address,
                         arrival_address,
                         'mtw-tariff-name',
                         'mtw-tariff-price')

    def parse(self, driver):
        driver.get("https://city-mobil.ru")

        button = driver.find_element_by_xpath("//button[contains(text(),'Заказать такси')]")
        button.click()

        wait = WebDriverWait(driver, 10)

        # Pick up
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[@placeholder='Откуда']")
        )).send_keys(self.pick_up_address)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//li[contains(text(),'{self.pick_up_address}')]")
        )).click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[@placeholder='Куда']")
        )).send_keys(self.arrival_address)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//li[contains(text(),'{self.arrival_address}')]")
        )).click()

        wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "mtw-tariff-group")
        ))

        self._tariffs = driver.find_elements_by_class_name('mtw-tariff-group')


class WeatherParser:
    def __init__(self, url="https://yandex.ru/pogoda/kazan"):
        self.url = url

    def get_weather(self, driver):
        driver.get(self.url)
        temperature = driver.find_element_by_css_selector(".temp.fact__temp .temp__value").text
        weather = driver.find_element_by_css_selector(".link__condition").text
        return {
            "temperature": int(temperature),
            "weather": weather,
        }
