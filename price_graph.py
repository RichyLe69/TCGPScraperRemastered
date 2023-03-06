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


# def find_lines_of_all_input(card_name, lines):
#     list_of_line_nums = []
#     for line_num, line in enumerate(lines):
#         if card_name in line:
#             list_of_line_nums.append(line_num)
#     return list_of_line_nums


# def extract_date_from_string(string):
#     # Year-Month-Day
#     regex = r'\d{4}-\d{2}-\d{2}'
#     date = re.findall(regex, string)[0]
#     return date


# def get_date_of_respective_line(line_number, price_table):
#     search_string = "--------"
#     table_border_match_count = 0
#     while table_border_match_count != 2:
#         line_number -= 1
#         if search_string in price_table[line_number]:
#             table_border_match_count += 1
#     if table_border_match_count == 2:
#         date_row_number = line_number - 1
#         date = extract_date_from_string(price_table[date_row_number])
#     return date


# def get_number_out_of_string(line):
#     line = line.split('|', 2)[2]
#     exclude_string = "1st"
#     number = int(re.findall(r'\d+', re.sub(exclude_string, '', line))[0])
#     return number

# def get_date_price_value_list(lines, price_table):
#     data_point = []  # [date, value]
#     for nums in lines:
#         value = get_number_out_of_string(price_table[nums])
#         date = get_date_of_respective_line(nums, price_table)
#         if value > 1:
#             data_point.append([date, value])  # should be chronological. Filters out 0 data
#     return data_point


# def get_closest_date_from_current_date(date_list, delta_days):
#     closest_index = 0
#     last_date = datetime.datetime.strptime(date_list[-1], '%Y-%m-%d')
#     target_date = last_date - datetime.timedelta(days=delta_days)
#     closest_date = datetime.datetime.strptime(date_list[0], '%Y-%m-%d')
#     for index, date_str in enumerate(date_list):
#         date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
#         if abs(date_obj - target_date) < abs(closest_date - target_date):
#             closest_date = date_obj
#             closest_index = index
#     return closest_date, int(closest_index)


# def calculate_difference_between_timedelta(dates, values, timedelta):  # Need
#     closest_date, closest_index = get_closest_date_from_current_date(dates, timedelta)
#     percent_diff, difference = calculate_percentage_difference(values[-1], values[closest_index])
#     perc_diff_data_formatted_string = ('{}: {} - {}'.format(convert_raw_days_to_simplified_notation(timedelta),
#                                                             format_difference_string(difference, percent_diff),
#                                                             closest_date.date()))
#     return difference, percent_diff, perc_diff_data_formatted_string


# def convert_raw_days_to_simplified_notation(days):
#     string_dict = {7: '1W', 14: '2W', 30: '1M', 60: '2M', 90: '3M', 180: '6M', 365: '1Y', 730: '2Y', 1460: '4Y'}
#     return string_dict[days]


# def format_difference_string(diff, percent_diff):
#     if percent_diff > 0:
#         return '+{} (+{}%) {}'.format(diff, percent_diff, '\u2191')
#     else:
#         return '{} ({}%) {}'.format(diff, percent_diff, '\u2193')


# def calculate_percentage_difference(current_value, old_value):
#     percentage_diff = (current_value - old_value) / old_value * 100
#     percentage_diff = round(percentage_diff, 1)
#     difference = current_value - old_value
#     return percentage_diff, difference


def get_text_color(string):
    if '\u2191' in string:
        return 'Green'
    elif '\u2193' in string:
        return 'Red'


def get_price_graph(card_name):
    pricing_variable_full = [['min_prices_sorted.txt', 'Min'],
                             ['max_prices_sorted.txt', 'Max'],
                             ['mean_prices_sorted.txt', 'Mean'],
                             ['median_prices_sorted.txt', 'Median']]  # 2023 and onwards

    # pricing_variable_full = [['/garb/lowest_prices_sorted.txt', 'lowest'],
    #                          ['/garb/last_sold_sorted.txt', 'last sold'],
    #                          ['/garb/market_prices_sorted.txt', 'market prices']]  # 2021 May - 2022 Nov
    #
    # pricing_variable_full = [['/garb/2020 May - 2021 April archive/market_prices_sorted.txt', 'market prices']]

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
    get_price_graph('Judgment Dragon')

# Script will generate a graph based on card name and pricing_variable_full
#       Simply select which time period you want to scrape from.
#  python .\price_graph.py
