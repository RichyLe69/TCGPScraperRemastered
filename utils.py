from datetime import datetime
from bs4 import BeautifulSoup
import time
import prettytable
import yaml
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from csv import DictWriter
import os
import re
import statistics

# base_url = 'https://store.tcgplayer.com/admin/product/manage/'
base_url = 'https://www.tcgplayer.com/product/'
current_date = str(datetime.date(datetime.now()))
current_year_full = datetime.now().strftime('%Y')  # 2018
current_month = datetime.now().strftime('%m')  # 02 //This is 0 padded
current_month_text = datetime.now().strftime('%h')  # Feb
current_day = datetime.now().strftime('%d')  # // 23 //This is also padded


def condition_edition_url_filters(condition_edition, language='english', photos=False):
    if language == 'english':
        language = '?Language=English'

    if '1st' in condition_edition:
        edition = '&Printing=1st+Edition'
    elif 'Unlimited' in condition_edition:
        edition = '&Printing=Unlimited'
    elif 'Limited' in condition_edition:
        edition = '&Printing=Limited'
    else:
        edition = '&Printing=Unlimited'

    if 'Near Mint' in condition_edition:
        condition = '&Condition=Near+Mint'
    elif 'Lightly Played' in condition_edition:
        condition = '&Condition=Lightly+Played'
    elif 'Moderately Played' in condition_edition:
        condition = '&Condition=Moderately+Played'
    else:
        condition = '&Condition=Near+Mint'

    if not photos:
        list_type = '&ListingType=standard'

    return language, edition, condition, list_type


def scrape_website(card_data_yaml, list_name, browser):
    delete_console_txt()
    start = time.time()
    file_path = ''

    # first = True
    timer = 10
    # lowest_listed_price_total = 0
    # last_sold_price_total = 0
    # market_price_total = 0
    total_card_quantity = 0
    max_price_total = 0
    min_price_total = 0
    mean_price_total = 0
    median_price_total = 0

    for card in card_data_yaml:
        condition_edition = card_data_yaml[card]['edition']
        card_quantity = card_data_yaml[card]['qty']

        url_mod = condition_edition_url_filters(condition_edition)
        url = '{}{}{}{}{}{}'.format(base_url, card_data_yaml[card]['url'], url_mod[0], url_mod[1], url_mod[2],
                                    url_mod[3])
        browser.get(url)

        try:
            viewing_present = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CLASS_NAME, 'product-details__listings')))
            time.sleep(6)
            no_table = False
        except:
            output_to_txt_console('Timeout No Results for: {}'.format(card))
            no_table = True

        if no_table:
            continue  # increments to the next element in for loop.

        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(['script', 'style']):
            script.extract()

        current_price_point_text = extract_listing_prices(soup)
        # text_only = extract_text_only(soup, condition_edition)  # data table with the prices we want to extract
        # data_prices = extract_data_prices(current_price_point_text, card)  # List[] 0 = Lowest listing, 1 = Last Sold, 2 = Market Price
        data_prices_new = calculate_data_prices(current_price_point_text, card)

        max_price_total += data_prices_new[0] * card_quantity
        min_price_total += data_prices_new[1] * card_quantity
        mean_price_total += data_prices_new[2] * card_quantity
        median_price_total += data_prices_new[3] * card_quantity

        # lowest_listed_price_total += (data_prices[0] * card_quantity)
        # last_sold_price_total += (data_prices[1] * card_quantity)
        # market_price_total += (data_prices[2] * card_quantity)
        total_card_quantity += card_quantity

        price_yaml_generator(card, data_prices_new[0], 'sorted_pricing/max_prices.yaml')
        price_yaml_generator(card, data_prices_new[1], 'sorted_pricing/min_prices.yaml')
        price_yaml_generator(card, data_prices_new[2], 'sorted_pricing/mean_prices.yaml')
        price_yaml_generator(card, data_prices_new[3], 'sorted_pricing/median_prices.yaml')

        my_table = create_pretty_table(data_prices_new)
        file_path = output_to_txt(card, my_table, card_quantity, condition_edition, list_name, data_prices_new[4])

    output_to_txt_console('Sum of Max Listed: ${:,.2f}'.format(max_price_total))
    output_to_txt_console('Sum of Min Listed: ${:,.2f}'.format(min_price_total))
    output_to_txt_console('Sum of Mean Listed: ${:,.2f}'.format(mean_price_total))
    output_to_txt_console('Sum of Median Listed: ${:,.2f}'.format(median_price_total))
    done = time.time()
    print(done - start)
    return file_path, [max_price_total, min_price_total, mean_price_total, median_price_total], total_card_quantity


def write_to_excel(column_names, price_dict, csv_name):
    # Top Row, list of column names

    with open(csv_name, 'a') as f_object:
        dict_writer_object = DictWriter(f_object, fieldnames=column_names)
        dict_writer_object.writerow(price_dict)
        f_object.close()


def price_yaml_generator(card_name, price, yaml_name):
    with open(yaml_name, 'r') as stream:
        current_yaml = yaml.safe_load(stream)
        # current_yaml = yaml.load(stream)
        current_yaml.update({card_name: price})

    with open(yaml_name, 'w') as stream:
        yaml.safe_dump(current_yaml, stream)
    return 0


def delete_console_txt():
    console = 'sorted_pricing/console.txt'
    with open(console, 'w') as f:
        f.write('')


def output_to_txt_console(string):
    print(string)
    txt_console = 'sorted_pricing/console.txt'
    with open(txt_console, 'a') as my_file:
        my_file.write(string + '\n')


def output_to_txt(card_name, my_table, card_quantity, condition_edition, list_name, num_listings):
    yaml_name = list_name + '-' + current_date + '.txt'
    directory = 'full_listings/{0}/{1}-{2}/{3}'.format(current_year_full,
                                                       current_month,
                                                       current_month_text,
                                                       current_day)
    try:
        os.makedirs(directory)
    except FileExistsError:
        pass  # directory already exists

    full_listing_file_path = 'full_listings/{0}/{1}-{2}/{3}/{4}'.format(current_year_full,
                                                                        current_month,
                                                                        current_month_text,
                                                                        current_day, yaml_name)
    with open(full_listing_file_path, 'a') as my_file:
        my_file.write('{0} [{1}] - {2} <{3}>\n'.format(card_name, card_quantity, condition_edition, num_listings))
        my_file.write(str(my_table) + '\n\n')
        return full_listing_file_path


def create_pretty_table(data_prices):
    my_table = prettytable.PrettyTable(['Max', 'Min', 'Mean', 'Median'])
    my_table.add_row([data_prices[0], data_prices[1], data_prices[2], data_prices[3]])
    return my_table


def calculate_data_prices(price_table, card):
    if not price_table:
        print('No data found for {}'.format(card))
        output_to_txt_console('Missing Data for:    {}'.format(card))
        return 0, 0, 0, 0, 0
    card_prices = []
    for item in price_table:
        card_prices.append(int(item[0]))

    max_val = (max(card_prices))
    min_val = (min(card_prices))
    mean_val = int((sum(card_prices) / len(card_prices)))
    median_val = (statistics.median(card_prices))
    num_listings = len(price_table)
    # print('{} - Max: {}, Min: {}, Mean: {}, Median: {}, # Listings: {}'.format(card, max_val, min_val, mean_val, median_val, num_listings))
    return max_val, min_val, mean_val, median_val, num_listings


# def extract_data_prices(price_table, card):
#     data_list = []
#     num_dollar_sign = 1
#     for character_index in range(0, len(price_table)):
#         if price_table[character_index] == '-':
#             if num_dollar_sign == 1:
#                 output_to_txt_console('Missing [0] TCG Lowest for:    {}'.format(card))
#             if num_dollar_sign == 3:
#                 output_to_txt_console('Missing [1] TCG Last Sold for: {}'.format(card))
#             if num_dollar_sign == 5:
#                 output_to_txt_console('Missing [2] Market Price for:  {}'.format(card))
#             data_list.append(0)
#             num_dollar_sign += 2
#         if price_table[character_index] == '$':
#             if num_dollar_sign == 1 or num_dollar_sign == 3 or num_dollar_sign == 5:
#                 data_list.append(dollar_string_to_int(price_table[character_index:character_index + 5].split('.')[0]))
#             num_dollar_sign += 1
#         if num_dollar_sign > 5:
#             return data_list
#     return data_list


def get_card_lists(yaml_name):
    with open(yaml_name, 'r') as stream:
        try:
            card_lists = yaml.safe_load(stream)
        except yaml.YAMLError:
            pass
        return card_lists


def extract_listing_prices(raw_html):
    text_only = raw_html.get_text()
    text_only = text_only.split('Ship To UNITED STATES')[1].split('TCGplayer Core Value')[0]

    list = []
    x = text_only.split('Shipping')
    for item in x:
        item = item.replace('\n', '')
        list.append(item)

    for item in list:
        if '$' not in item:
            list.remove(item)

    second_list = []
    for x in range(0, len(list)):
        second_list.append([0, 0, 0])

    # Get Card Price
    x = 0
    for item in list:
        price = item.split('$')[1].split('.')[0].replace(',', '')
        try:
            second_list[x][0] = int(price)
        except ValueError:
            print('Value Error for this price. Skipping it')
            second_list[x][0] = second_list[x-1][0]
        x += 1

    # Get Seller # Sales
    x = 0
    for item in list:
        try:
            seller_stats = item.split('Sales)')[0].split('(')[1]
        except IndexError:
            print('Index Error for Seller Stats. Skipping')
            second_list[x][1] = 0
        second_list[x][1] = seller_stats
        x += 1

    # Get Seller % Stat
    x = 0
    for item in list:
        percent_index = item.find('%')
        percent_lower_bound = percent_index - 4
        seller_percent = item[percent_lower_bound:percent_index]
        result = re.sub(r'[^0-9\.]', '', seller_percent)
        second_list[x][2] = result
        x += 1

    return second_list


# def extract_text_only(input_html, edition):
#     # Extracts data table starting from edition
#     # lowest listing (1st dollar), last sold listing (3rd dollar), market price( 5th dollar)
#     start = edition  # First word before price table
#     end = 'Browsing as Yuginag'  # Last word of page
#     text_only = input_html.get_text()
#     text_only = text_only.strip('\n')
#     text_only = text_only.strip('')
#     text_only = text_only.replace('\n', ' ')
#     text_only = text_only.replace('  ', ' ')
#     try:
#         text_only = text_only.split(start)[1]
#     except IndexError:
#         print(text_only)
#     try:
#         text_only = text_only.split(end)[0]
#     except IndexError:
#         print(text_only)
#     return text_only


def dollar_string_to_int(dollar_string):
    dollar_string = dollar_string.replace('$', '')
    return int(dollar_string)


def sort_market_prices(yaml_name, name):
    with open(yaml_name, 'r') as stream:
        try:
            yaml_data = yaml.safe_load(stream)
            card_list = list()
            for cards in yaml_data:
                card_list.append(cards)
        except yaml.YAMLError:
            pass
    yaml_data = yaml_data

    prices_sorted = {k: v for k, v in sorted(yaml_data.items(), key=lambda x: x[1], reverse=True)}

    my_table = prettytable.PrettyTable(['Card', 'Price'])

    for card in prices_sorted:
        my_table.add_row([card, prices_sorted[card]])

    sorted_yaml = yaml_name.replace('.yaml', '') + '_sorted.txt'
    with open(sorted_yaml, 'a') as my_file:
        my_file.write(str(name) + ' - ' + str(current_date) + '\n')
        my_file.write(str(my_table) + '\n')
    delete_yaml_contents(yaml_name)
    return 0


def delete_yaml_contents(yaml_name):
    test_dict = {'test': 0}
    with open(yaml_name, 'w') as stream:
        yaml.safe_dump(test_dict, stream)


def append_console_to_txt(path):
    console = 'sorted_pricing/console.txt'
    with open(console, 'r') as console:
        console_data = console.read()
    with open(path, 'r') as original:
        data = original.read()
    with open(path, 'w') as modified:
        modified.write(console_data + "\n" + data)
    delete_console_txt()


def sum_total_prices(current_sums, list_of_sums):
    current_sums[0] = current_sums[0] + list_of_sums[0]  # Max
    current_sums[1] = current_sums[1] + list_of_sums[1]  # Min
    current_sums[2] = current_sums[2] + list_of_sums[2]  # Mean
    current_sums[3] = current_sums[3] + list_of_sums[3]  # Median
    return current_sums


def sum_total_quantity(current_quantity, quantity_of_list):
    return current_quantity + quantity_of_list


def calculate_average_per_list(sums, quantity):
    Max = sums[0] / quantity
    Min = sums[1] / quantity
    Mean = sums[2] / quantity
    Median = sums[3] / quantity
    print('Total Quantity: {}'.format(quantity))
    print('Average of Max: {}'.format('{:.1f}'.format(Max)))
    print('Average of Min: {}'.format('{:.1f}'.format(Min)))
    print('Average of Mean: {}'.format('{:.1f}'.format(Mean)))
    print('Average of Median: {}'.format('{:.1f}'.format(Median)))


def print_sums(sums):
    print('Sum of Max: {}'.format(sums[0]))
    print('Sum of Min: {}'.format(sums[1]))
    print('Sum of Mean: {}'.format(sums[2]))
    print('Sum of Median: {}'.format(sums[3]))
    print('[{}, {}, {}, {}]'.format(human_format(sums[0]), human_format(sums[1]), human_format(sums[2]), human_format(sums[3])))


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:.1f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def create_excel_column_names(card_list):
    data_list = []
    data_list.append('DATE')
    for card in card_list:
        data_list.append(card)
    return data_list
