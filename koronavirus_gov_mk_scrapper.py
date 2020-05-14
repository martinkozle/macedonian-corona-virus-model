import logging
import sys
import json
from seleniumwire import webdriver  # used to get the background requests
from selenium.common.exceptions import TimeoutException
from time import sleep
import csv


class Scrapper:

    def __init__(self, *, debug=False):
        self.data = []
        self._site_url = 'https://koronavirus.gov.mk/stat'
        self._debug = debug
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(level=logging.DEBUG if debug else logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    # returns a Selenium webdriver based on headless Chrome
    @staticmethod
    def _headless_chrome_driver() -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        driver = webdriver.Chrome(options=options)
        return driver

    # full chrome webdriver for debugging
    @staticmethod
    def _chrome_driver() -> webdriver.Chrome:
        return webdriver.Chrome()

    def _get_data(self):
        driver = None
        response_body_json = None
        try:
            self._logger.debug('Opening Chrome webdriver')
            if self._debug:
                driver = self._chrome_driver()
            else:
                driver = self._headless_chrome_driver()
            self._logger.debug('Requesting ' + self._site_url)
            driver.get(self._site_url)
            self._logger.debug('Waiting for 15 seconds for website to load')
            sleep(15)  # site is super slow to load
            # get api data
            for request in driver.requests:
                if request.response and 'https://datastudio.google.com/embed/batchedDataV2' in request.path:
                    request_body_json = json.loads(request.body.decode('utf-8'))
                    if len(request_body_json['dataRequest']) == 5:
                        self._logger.debug('Found request that contains required data')
                        response_body_json = json.loads(request.response.body.decode('utf-8')[6:])
                        break
        except TimeoutException:
            self._logger.error('Request timed out, check if {} is up.'.format(self._site_url))
        except Exception as err:
            self._logger.exception(err)
        finally:
            if driver:
                driver.quit()
        return response_body_json

    def scrape(self):
        self._logger.debug('Data gathering started')
        raw_data = self._get_data()
        if not raw_data:
            self._logger.error("Didn't manage to find the data from requests")
            return
        data_response = raw_data['default']['dataResponse'][1]['dataSubset'][0]['dataset']['tableDataset']['column']
        dates = list(map(int, data_response[0]['stringColumn']['values']))
        total_infected, total_cured, total_deaths = (list(map(int, data_response[i]['doubleColumn']['values']))
                                                     for i in range(1, 4))
        self.data = list(zip(dates, total_infected, total_cured, total_deaths))

    def write_to_csv_file(self, *, destination=None):
        if not destination:
            destination = 'data/data_{}.csv'.format(self.data[-1][0])  # get last date
        self._logger.debug('Writing data to {}'.format(destination))
        with open(destination, 'w', newline='') as f:
            csv_writer = csv.writer(f)
            for row in self.data:
                csv_writer.writerow(row)


def main():
    scrapper = Scrapper(debug=True)
    scrapper.scrape()
    scrapper.write_to_csv_file()


if __name__ == '__main__':
    main()
