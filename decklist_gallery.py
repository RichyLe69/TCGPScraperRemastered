import os
import cv2
import numpy as np
from utils import get_card_lists, get_number_out_of_string
from CardList import CardList
from prettytable import PrettyTable
from datetime import datetime
import datetime

# Configs
use_max_rarity_pricing = True
display_rarity_in_decklist = True
generate_decklist_gallery = True
generate_decklist_prices = True


# Generating Decklist Gallery #


def calculate_row_cols(deck_of_decoded_cards, image_name):
    if len(deck_of_decoded_cards) > 40:
        rows = min(int(len(deck_of_decoded_cards) / 10) + 1, 6)
        cols = 10
    else:
        rows, cols = 4, 10
    if image_name in ['Side', 'Extra']:
        rows, cols = 1, 15
    return rows, cols


def get_full_deck_list_image_paths(deck_of_decoded_cards):
    full_deck_list_image_paths = []
    path_to_card_images = "decks/decklists/raw_imgs"  # root directory of images
    for current_card in deck_of_decoded_cards:  # For every card in my deck
        current_card = current_card + '.jpg'
        card_image_found = False
        for dirpath, dirnames, list_of_images in os.walk(path_to_card_images):  # check in every folder card
            for file in list_of_images:
                if current_card == file:
                    card_image_found = True
                    image_paths = [os.path.join(dirpath, current_card)]
                    full_deck_list_image_paths.append(image_paths)
                    break
        if not card_image_found:
            print('Image Not Found: {}'.format(current_card))  # Card must be in card_code_list.yaml

    return full_deck_list_image_paths


def create_grid_image(deck_of_decoded_cards, image_name):
    rows, cols = calculate_row_cols(deck_of_decoded_cards, image_name)
    image_width = 450
    image_height = 657
    canvas_width = 310 if image_name in ('Side', 'Extra') else image_width
    final_image = np.zeros((rows * image_height, cols * canvas_width, 3), dtype=np.uint8)

    full_deck_list_image_paths = get_full_deck_list_image_paths(deck_of_decoded_cards)
    for i in range(rows * cols):
        try:
            img = cv2.imread(full_deck_list_image_paths[i][0])
        except IndexError:
            break
        img = cv2.resize(img, (image_width, image_height))

        row = i // cols
        col = i % cols

        y_start = row * image_height
        y_end = y_start + image_height
        x_start = int((col * image_width) * (2 / 3)) if image_name in ('Side', 'Extra') else (col * image_width)

        x_end = (x_start + image_width)
        final_image[y_start:y_end, x_start:x_end, :] = img

    if image_name in ('Side', 'Extra'):
        final_image = cv2.resize(final_image, (4500, 657))
    return final_image


def check_if_max_rarity(card_code_list, node, cards, decode):  # Check for Rarity String Overwrite
    if isinstance(card_list_in_deck[node][cards], str):  # Other Rarity
        qty, different_rarity = card_list_in_deck[node][cards].split(' ')  # [Num, Rarity]
        different_rarity = '-' + different_rarity + '-'
        for x, diff_rarities in enumerate(card_code_list[decode]):
            if different_rarity in diff_rarities:
                card_to_add = card_code_list[decode][x]  # decoded card, selected rarity
    else:  # Max Rarity
        card_to_add = card_code_list[decode][0]  # decoded card, max rarity
        qty = card_list_in_deck[node][cards]
    return card_to_add, qty


def get_nodes_to_do(img_name):
    nodes_to_do = {'Main': ['Monsters', 'Spells', 'Traps'],
                   'Side': ['Side'],
                   'Extra': ['Extra']}
    return nodes_to_do[img_name]


def generate_image(card_list_in_deck, img_name):
    for node in card_list_in_deck:  # Monster, Spells, Traps, Side, Extra
        nodes_to_do = get_nodes_to_do(img_name)

        list_of_cards_to_append = []
        if node != 'Header':
            if node in nodes_to_do:
                for cards in card_list_in_deck[node]:  # Card from deck list
                    if cards == 'None':
                        return None
                    match = False
                    for decode in card_code_list:  # Decoded english name of decode cards
                        if cards == decode:
                            match = True
                            card_to_add, qty = check_if_max_rarity(card_code_list, node, cards, decode)
                            for x in range(0, int(qty)):
                                list_of_cards_to_append.append(card_to_add)
                    if not match:
                        print('Card Missing from card_code_list.yaml: {}'.format(cards))
            deckbuilder.extend_to_deck_of_decoded_cards(list_of_cards_to_append)
    final_image = create_grid_image(deckbuilder.get_deck_of_decoded_cards(), img_name)
    deckbuilder.reset_deck_of_decoded_cards()
    return final_image


def place_header_on_decklist(full_image, header):
    font = cv2.FONT_HERSHEY_TRIPLEX
    font_scale = 4
    color = (255, 255, 255)  # White
    thickness = 5
    height, width = full_image.shape[:2]
    canvas = np.zeros((height + 200, width, 3), dtype=np.uint8)
    canvas[:height, :] = full_image
    canvas = cv2.putText(canvas, header, (50, height+135), font, font_scale, color, thickness)
    return canvas


def combine_images(main_image, side_image, extra_image, deck_list_name, header):
    pics_to_combine = list(filter(lambda x: x is not None, [main_image, side_image, extra_image]))
    combined_pic = cv2.vconcat(pics_to_combine)
    final_image_with_header = place_header_on_decklist(combined_pic, header)
    cv2.imwrite('RemasteredDeckLists/' + deck_list_name + '.jpg', final_image_with_header)


# Generating Price Table #


def get_card_value_data_table(collection_name, list_name):
    price_table_path_root = 'sorted_pricing/'
    final_data_table = ''

    with open(price_table_path_root + list_name, 'r') as file:
        lines = file.readlines()
        for coll in collection_name:
            final_data_table += (get_data_table_of_last_instance(coll, lines))

    return final_data_table


def get_line_of_last_instance(collection_name, full_data):
    line_number = 0
    last_line_number = None
    for line in full_data:
        line_number += 1
        if collection_name in line:
            last_line_number = line_number
    return last_line_number


def get_last_line_of_last_instance(full_data, start_line):
    search_string = "--------"
    line_numbers = []

    line_number = 0
    for line in full_data:
        if line_number >= start_line and search_string in line:
            line_numbers.append(line_number)
            if len(line_numbers) >= 3:
                break
        line_number += 1
    end_of_table_line = line_number

    return end_of_table_line


def get_data_table_between_first_last_lines(full_data, first_line, last_line):
    data = ""
    for line_number, line in enumerate(full_data):
        if first_line <= line_number <= last_line:
            data += line
    return data


def get_data_table_of_last_instance(collection_name, full_data):
    first_line = get_line_of_last_instance(collection_name, full_data)
    last_line = get_last_line_of_last_instance(full_data, first_line)
    data_table = get_data_table_between_first_last_lines(full_data, first_line, last_line)
    return data_table


def get_rarity_from_card_code(card):
    for decode in card_code_list:  # Decoded english name of decode cards
        if card == decode:
            return card_code_list[card][0].split('-')[3]
    print('Card missing from card_code_list, unable to get Rarity: {}'.format(card))
    return 'ERR'


def get_card_quantity_rarity(card_list_in_deck, node, cards):
    if isinstance(card_list_in_deck[node][cards], str):  # Other Rarity
        extracted_data = card_list_in_deck[node][cards].split(' ')  # [Num, Rarity, Edition]
        qty, rarity = int(extracted_data[0]), extracted_data[1]
        rarity_overwrite = True
    else:
        qty = int(card_list_in_deck[node][cards])
        rarity = get_rarity_from_card_code(cards)
        rarity_overwrite = False

    if use_max_rarity_pricing:
        rarity_overwrite = False
    return qty, rarity, rarity_overwrite


def search_thru_price_data_for_card(card_list_in_deck, most_recent_price_data):
    most_recent_price_data = most_recent_price_data.split('\n')
    noded_prices = {}
    prices = {}
    for node in card_list_in_deck:  # Monster, Spells, Traps, Side, Extra
        if node != 'Header':
            for cards in card_list_in_deck[node]:  # Card from deck list
                match = False
                qty, rarity, rarity_overwrite = get_card_quantity_rarity(card_list_in_deck, node, cards)
                for line in most_recent_price_data:
                    if cards in line and (not rarity_overwrite or (rarity_overwrite and rarity in line)):
                        match = True
                        value = get_number_out_of_string(line)
                        if cards not in prices:
                            prices[cards] = [value, qty, rarity]
                        else:
                            prices[cards] = [max(value, prices[cards][0]), qty, rarity]
                if not match:
                    # pass
                    print('Card not in Sorted Price Table. Wrong name in collection.yaml?: {}'.format(cards))
                    prices[cards] = ['-', qty, rarity]
            noded_prices[node] = prices
            prices = {}
    return noded_prices


def generate_pretty_table_decklist_price(full_deck_prices, deck_list_name, pricing_variable):
    value_index, qty_index, rarity_index = 0, 1, 2
    sectional_prices = {}
    my_table = PrettyTable(['Card', '$'])
    my_table.align = 'l'
    my_table.align['$'] = 'r'

    for node in full_deck_prices:
        sectional_value = 0
        splitter = False
        main_already = False
        for card in full_deck_prices[node]:
            qty = full_deck_prices[node][card][qty_index]
            val_object = full_deck_prices[node][card][value_index]
            value = val_object if isinstance(val_object, int) else 0
            rarity = full_deck_prices[node][card][rarity_index] if display_rarity_in_decklist else ''
            if node == 'Monsters' and not main_already or node == 'Side' or node == 'Extra':
                if not splitter:
                    if node == 'Monsters' and not main_already:
                        my_table.add_row(['Main Deck', ''])
                        main_already = True
                    else:
                        my_table.add_row(['\n' + node + ' Deck', ''])
                        splitter = True
            sectional_value += (value * qty)
            value = '-' if value == 0 else value
            my_table.add_row(['{} {} {}'.format(qty, card, rarity), value])
        sectional_prices[node] = sectional_value

    main_deck_value = sectional_prices['Monsters'] + sectional_prices['Spells'] + sectional_prices['Traps']
    side_deck_value = sectional_prices['Side']
    extra_deck_value = sectional_prices['Extra']
    total_deck_value = main_deck_value + side_deck_value + extra_deck_value
    summed_totals = ('Main Deck: {}\n'
                     'Side Deck: {}\n'
                     'Extra Deck: {}\n'
                     'Total Price: {}'.format(main_deck_value, side_deck_value, extra_deck_value, total_deck_value))

    directory = 'RemasteredDeckLists/decklist prices/'
    file_name = deck_list_name + '.txt'
    current_date = str(datetime.datetime.date(datetime.datetime.now()))
    with open(directory + file_name, 'a') as my_file:
        my_file.write(str(deck_list_name) + ' - ' + str(current_date) + ' - ' + pricing_variable + '\n')
        my_file.write(str(summed_totals) + '\n')
        my_file.write(str(my_table) + '\n')


class DeckBuilder:
    def __init__(self):
        self.list_of_decks = get_card_lists('decks/decklists/list_of_decks.yaml')
        self.card_code_list = get_card_lists('decks/decklists/card_code_list.yaml')

        self.current_list = ''
        self.list_name = ''
        self.yaml_data = ''
        self.path = ''
        self.deck_of_decoded_cards = []
        self.alphabetical_order = False

    def get_list_of_decks(self):
        return self.list_of_decks

    def get_card_code_list(self):
        return self.card_code_list

    def get_list_name(self):
        return self.list_name

    def get_yaml_data(self):
        return self.yaml_data

    def get_header(self):
        header = ''
        try:
            header = (self.get_yaml_data()['Header'])
        except KeyError:
            print('Header not found.')
        return header

    def extend_to_deck_of_decoded_cards(self, decoded_card_input):
        if not decoded_card_input:
            return
        if self.alphabetical_order:
            decoded_card_input = sorted(decoded_card_input, reverse=False)
        self.deck_of_decoded_cards.extend(decoded_card_input)

    def get_deck_of_decoded_cards(self):
        return self.deck_of_decoded_cards

    def reset_deck_of_decoded_cards(self):
        self.deck_of_decoded_cards = []

    def get_yaml_list_data(self, current_deck_list, full_card_lists):
        self.current_list = CardList(full_card_lists[current_deck_list]['path'], current_deck_list)
        self.list_name = (self.current_list.get_list_name())
        self.yaml_data = (self.current_list.get_yaml_data())
        self.path = (self.current_list.get_path())


if __name__ == '__main__':
    deckbuilder = DeckBuilder()
    list_of_decks = deckbuilder.get_list_of_decks()
    card_code_list = deckbuilder.get_card_code_list()

    collection_name = ['collection_deck_builder', 'collection_deck_core',
                       'collection_extra_deck', 'collection_old_school',
                       'buylist_2007_08_max_deck', 'buylist_cool_singles_t2',
                       'buylist_edison', 'buylist_lightswornrulers',
                       ]
    pricing_variable_full = ['min_prices_sorted.txt', 'max_prices_sorted.txt',
                             'mean_prices_sorted.txt', 'median_prices_sorted.txt']  # Full
    # pricing_variable_full = ['min_prices_sorted.txt']  # Single

    for current_deck_list in list_of_decks:
        deckbuilder.get_yaml_list_data(current_deck_list, list_of_decks)
        deck_list_name = deckbuilder.get_list_name()
        card_list_in_deck = deckbuilder.get_yaml_data()

        # # Generate Decklist Gallery
        if generate_decklist_gallery:
            header = deckbuilder.get_header()
            combine_images(generate_image(card_list_in_deck, 'Main'),
                           generate_image(card_list_in_deck, 'Side'),
                           generate_image(card_list_in_deck, 'Extra'),
                           deck_list_name, header)

        # # Generate Decklist Prices
        if generate_decklist_prices:
            for pricing_variable in pricing_variable_full:
                most_recent_price_data = get_card_value_data_table(collection_name, pricing_variable)
                full_deck_prices = search_thru_price_data_for_card(card_list_in_deck, most_recent_price_data)
                generate_pretty_table_decklist_price(full_deck_prices, deck_list_name, pricing_variable)

# To Run PS C:\Users\Richard Le\PycharmProjects\SellerPortalDatabase> python .\decklist_gallery.py
#       Updates new text data based on already scraped .txt database. Recommended running after price scraping (weekly)
