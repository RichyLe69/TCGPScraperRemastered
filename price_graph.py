from datetime import datetime  # Goes first
import datetime  # Goes Second
import matplotlib.dates
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, VPacker
from mplcursors import cursor
from decklist_gallery import DeckBuilder
from utils import find_lines_of_all_input, get_date_price_value_list, calculate_difference_between_timedelta


# Price Graph Chart

def get_rarity_from_card_code(card):  # Duplicate Func
    for decode in card_code_list:  # Decoded english name of decode cards
        if card == decode:
            return card_code_list[card][0].split('-')[3]
    print('Card missing from card_code_list, unable to get Rarity: {}'.format(card))
    return 'ERR'


def get_text_color(string):
    if '\u2191' in string:
        return 'Green'
    elif '\u2193' in string:
        return 'Red'


def get_pricing_time_period(year):
    pricing_variable_full = {
        2020: [['/garb/2020 May - 2021 April archive/market_prices_sorted.txt', 'market prices']],
        2021: [['/garb/lowest_prices_sorted.txt', 'lowest'],
               ['/garb/last_sold_sorted.txt', 'last sold'],
               ['/garb/market_prices_sorted.txt', 'market prices']]  # 2021 May - 2022 Nov
    }
    if year not in pricing_variable_full:
        pricing_variable_full = {
            year: [['min_prices_sorted.txt', 'Min'],
                   ['max_prices_sorted.txt', 'Max'],
                   ['mean_prices_sorted.txt', 'Mean'],
                   ['median_prices_sorted.txt', 'Median']]  # 2023 and onwards
        }
    return pricing_variable_full[year]


def get_price_graph(card_name):
    pricing_variable_full = get_pricing_time_period(2023)

    fig = plt.figure(figsize=(10, 5))

    data_lock = False
    difference_data_summary = []

    timedelta_list = [7, 14, 30, 60, 90, 180, 365, 730, 1460]
    for price_table in pricing_variable_full:
        price_table_path_root = 'sorted_pricing/'
        with open(price_table_path_root + price_table[0], 'r') as file:
            lines = file.readlines()  # Raw text taken from .txt
        line_numbers = find_lines_of_all_input(card_name, lines)
        plot_points = get_date_price_value_list(line_numbers, lines)
        dates = [item[0] for item in plot_points]
        values = [item[1] for item in plot_points]

        for delta in timedelta_list:
            difference, percent_diff, percent_diff_data_formatted_string, _ = calculate_difference_between_timedelta(dates, values, delta)
            if not data_lock:
                difference_data_summary.append(percent_diff_data_formatted_string)
        dates = [datetime.datetime.strptime(date, '%Y-%m-%d').date() for date in dates]
        plt.plot(dates, values, marker='.', label=price_table[1])
        data_lock = True

    ax = plt.subplot(111)
    ax.set_ylim(ymin=0)
    text_to_add = []
    for entry in difference_data_summary:
        color = get_text_color(entry)
        text_to_add.append(TextArea(entry, textprops=dict(color=color)))
    box = VPacker(children=text_to_add, align="left", pad=1, sep=1)
    anchored_box = AnchoredOffsetbox(loc=5, child=box, pad=0.1, frameon=True,
                                     bbox_to_anchor=(1, 0.20), bbox_transform=ax.transAxes, borderpad=0., )
    ax.add_artist(anchored_box)
    plt.gca().fmt_xdata = matplotlib.dates.DateFormatter("%d-%b-%Y")

    rarity = get_rarity_from_card_code(card_name)
    plt.title('{} {}'.format(card_name, rarity))
    plt.xlabel('Date')
    plt.ylabel('Value')
    cursor(hover=True)  # Allows hovering over points
    plt.legend()
    plt.show()


if __name__ == '__main__':
    deckbuilder = DeckBuilder()
    card_code_list = deckbuilder.get_card_code_list()
    get_price_graph('Necro Gardna')

# Script will generate a graph based on card name and pricing_variable_full
#       Simply select which time period you want to scrape from.
#       Provides on-demand data, based on already saved .txt database. Does not save any new data.

#  python .\price_graph.py
