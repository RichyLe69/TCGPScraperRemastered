from prettytable import PrettyTable
from decklist_gallery import DeckBuilder
from utils import convert_raw_days_to_simplified_notation, calculate_difference_between_timedelta, \
    get_date_price_value_list, find_lines_of_all_input, format_difference_string


def get_rarity_from_card_code(card):  # Duplicate Func
    for decode in card_code_list:  # Decoded english name of decode cards
        if card == decode:
            return card_code_list[card][0].split('-')[3]
    print('Card missing from card_code_list, unable to get Rarity: {}'.format(card))
    return 'ERR'


def price_data_dict(card_name):
    # pricing_variable_full = [['min_prices_sorted.txt', 'Min']]  # ,
    # ['max_prices_sorted.txt', 'Max'],
    # ['mean_prices_sorted.txt', 'Mean'],
    # ['median_prices_sorted.txt', 'Median']]  # 2023 and onwards

    pricing_variable_full = [['/garb/lowest_prices_sorted.txt', 'lowest']]#,
    #                          ['/garb/last_sold_sorted.txt', 'last sold'],
    #                          ['/garb/market_prices_sorted.txt', 'market prices']]  # 2021 May - 2022 Nov
    #
    # pricing_variable_full = [['/garb/2020 May - 2021 April archive/market_prices_sorted.txt', 'market prices']]

    card_price_data_dict = {card_name: {
        'rarity': '',
        'now_price': 0,
        '1W': 0,
        '2W': 0,
        '1M': 0,
        '2M': 0,
        '3M': 0,
        '6M': 0,
        '1Y': 0,
        '2Y': 0,
        '4Y': 0
    }}
    card_price_data_dict[card_name]['rarity'] = get_rarity_from_card_code(card_name)
    data_lock = False
    timedelta_list = [7, 14, 30, 60, 90, 180, 365, 730, 1460]
    closest_dates = {}
    for price_table in pricing_variable_full:
        price_table_path_root = 'sorted_pricing/'
        with open(price_table_path_root + price_table[0], 'r') as file:
            lines = file.readlines()  # Raw text taken from .txt
        line_numbers = find_lines_of_all_input(card_name, lines)
        plot_points = get_date_price_value_list(line_numbers, lines)
        dates = [item[0] for item in plot_points]
        values = [item[1] for item in plot_points]

        for delta in timedelta_list:
            difference, percent_diff, percent_diff_data_formatted_string, closest_date = calculate_difference_between_timedelta(dates,
                                                                                                                  values,
                                                                                                                  delta)
            if not data_lock:
                card_price_data_dict[card_name][convert_raw_days_to_simplified_notation(delta)] = [difference,
                                                                                                   percent_diff]
                card_price_data_dict[card_name]['now_price'] = values[-1]
                closest_dates.update(closest_date)
        data_lock = True
    return card_price_data_dict, closest_dates


def convert_price_change_list_to_string(price_change_list):
    return format_difference_string(price_change_list[0], price_change_list[1])


def add_row_to_format_list_table(card, item, table):
    full_data_list = []
    time_windows = ['1W', '2W', '1M', '2M', '3M', '6M', '1Y', '2Y', '4Y']
    for x in time_windows:
        full_data_list.append(convert_price_change_list_to_string(item[card][x]))
    card_data = [card, item[card]['rarity'], item[card]['now_price']]
    card_data.extend(full_data_list)
    table.add_row([*card_data])


def generate_format_history_table(list_of_cards):
    full_table = []
    for node in list_of_cards:
        if node == 'Header':
            continue
        for card in list_of_cards[node]:
            try:
                card_price_data_dict, closest_dates = price_data_dict(card)
                full_table.append(card_price_data_dict)
            except IndexError:
                pass

    my_table = PrettyTable(['Card', 'Rarity', 'Price',
                            '1W {}'.format(closest_dates['1W']),
                            '2W {}'.format(closest_dates['2W']),
                            '1M {}'.format(closest_dates['1M']),
                            '2M {}'.format(closest_dates['2M']),
                            '3M {}'.format(closest_dates['3M']),
                            '6M {}'.format(closest_dates['6M']),
                            '1Y {}'.format(closest_dates['1Y']),
                            '2Y {}'.format(closest_dates['2Y']),
                            '4Y {}'.format(closest_dates['4Y'])])
    my_table.align = 'l'
    my_table.align['$'] = 'r'

    sorted_list = sorted(full_table, key=lambda x: x[list(x.keys())[0]]['now_price'], reverse=True)  # Sort by Now Price
    for item in sorted_list:
        for card in item:
            add_row_to_format_list_table(card, item, my_table)
    return my_table


if __name__ == '__main__':
    deckbuilder = DeckBuilder()
    card_code_list = deckbuilder.get_card_code_list()
    list_of_decks = deckbuilder.get_list_of_decks()
    for current_deck_list in list_of_decks:
        deckbuilder.get_yaml_list_data(current_deck_list, list_of_decks)
        deck_list_name = deckbuilder.get_list_name()
        card_list_in_deck = deckbuilder.get_yaml_data()
        print(deck_list_name)
        print(generate_format_history_table(card_list_in_deck))


# Script will print out a table of all cards in deck lists, their pricing history.
# python .\format_list_generator.py
#       Provides on-demand data, based on already saved .txt database. Does not save any new data.
