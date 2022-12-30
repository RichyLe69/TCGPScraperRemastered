from utils import get_card_lists, scrape_website, sort_market_prices, append_console_to_txt, sum_total_prices, print_sums, sum_total_quantity, calculate_average_per_list
from CardList import CardList
from selenium import webdriver
import time


class Scraper:

    def __init__(self):
        self.browser = webdriver.Chrome(
            executable_path=r'C:\Users\Richard Le\PycharmProjects\SellerPortalDatabase\chromedriver.exe')
        self.card_lists = get_card_lists('lists.yaml')
        self.current_list = ''
        self.current_list_data = ''
        self.current_list_name = ''
        self.file_path = ''
        self.url = 'https://www.tcgplayer.com/product/33224'
        self.filters = '?Language=English&page=1&Condition=Near+Mint&ListingType=standard'
        self.sums = [0, 0, 0, 0]
        self.total_card_quantity = 0

    def get_card_list(self):
        return self.card_lists

    def open_link(self, link=''):
        if not link:
            self.browser.get(self.url)
        else:
            self.browser.get(link)

    def get_browser(self):
        return self.browser

    def wait_for_login(self) -> int:
        filler_char = input("Enter any key Selecting 50 view count: ")
        return 0

    def close_browser(self):
        self.browser.quit()

    def scrape_current_list(self, current_deck_list, full_card_lists):
        self.current_list = CardList(full_card_lists[current_deck_list]['path'], current_deck_list)
        self.current_list_data = self.current_list.get_yaml_data()
        self.current_list_name = self.current_list.get_list_name()
        self.file_path = scrape_website(self.current_list_data, self.current_list_name, scraper.get_browser())

    def sort_current_prices(self):
        sort_market_prices('sorted_pricing/max_prices.yaml', self.current_list_name)
        sort_market_prices('sorted_pricing/min_prices.yaml', self.current_list_name)
        sort_market_prices('sorted_pricing/mean_prices.yaml', self.current_list_name)
        sort_market_prices('sorted_pricing/median_prices.yaml', self.current_list_name)

    def output_sorted_prices(self):
        append_console_to_txt(self.file_path[0])

    def get_total_prices(self):
        self.sums = sum_total_prices(self.sums, self.file_path[1])  # List of [Sum Lowest, Sum Last, Sum Market]

    def get_sums(self):
        return self.sums

    def get_total_quantity(self):
        self.total_card_quantity = sum_total_quantity(self.total_card_quantity, self.file_path[2])

    def get_average_of_list(self):
        calculate_average_per_list(self.sums, self.total_card_quantity)


if __name__ == '__main__':

    scraper = Scraper()
    scraper.open_link()
    scraper.wait_for_login()
    card_lists = scraper.get_card_list()
    for split_lists in card_lists:
        scraper.scrape_current_list(split_lists, card_lists)
        scraper.sort_current_prices()
        scraper.output_sorted_prices()
        scraper.get_total_prices()
        scraper.get_total_quantity()
        time.sleep(1)
    scraper.close_browser()
    print_sums(scraper.get_sums())
    scraper.get_average_of_list()

# To Run PS C:\Users\Richard Le\PycharmProjects\SellerPortalDatabase> python .\main.py

# TODO
# individual consoles (to allow for multi processing)

# mysql table
# data calculations, graph creations
# get sums into graphable, plotable csv
