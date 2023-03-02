import os
import cv2
import numpy as np
from utils import get_card_lists
from CardList import CardList


def calculate_row_cols(deck_of_decoded_cards, image_name):
    if (len(deck_of_decoded_cards)) > 40:
        rows = min(int(len(deck_of_decoded_cards) / 10) + 1, 6)
        cols = 10
    else:
        rows = 4
        cols = 10
    if image_name == 'Side' or image_name == 'Extra':
        rows = 2
        cols = 10
    return rows, cols


def get_full_deck_list_image_paths(deck_of_decoded_cards):
    full_deck_list_image_paths = []
    path_to_card_images = "decks/decklists/img"  # root directory of images
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
            print('Image Not Found: {}'.format(current_card))
    return full_deck_list_image_paths


def create_grid_image(deck_of_decoded_cards, image_name):
    rows, cols = calculate_row_cols(deck_of_decoded_cards, image_name)
    image_width = 450
    image_height = 657
    final_image = np.zeros((rows * image_height, cols * image_width, 3), dtype=np.uint8)

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
        x_start = col * image_width
        x_end = x_start + image_width
        final_image[y_start:y_end, x_start:x_end, :] = img

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
    if img_name == 'Main':
        nodes_to_do = ['Monsters', 'Spells', 'Traps']
    if img_name == 'Side':
        nodes_to_do = ['Side']
    if img_name == 'Extra':
        nodes_to_do = ['Extra']
    return nodes_to_do


def generate_image(card_list_in_deck, img_name):
    for node in card_list_in_deck:  # Monster, Spells, Traps, Side, Extra
        nodes_to_do = get_nodes_to_do(img_name)

        list_of_cards_to_append = []
        if node != 'Header':
            if node in nodes_to_do:
                for cards in card_list_in_deck[node]:  # Card from deck list
                    match = False
                    for decode in card_code_list:  # Decoded english name of decode cards
                        if cards == decode:
                            match = True
                            card_to_add, qty = check_if_max_rarity(card_code_list, node, cards, decode)
                            for x in range(0, int(qty)):
                                list_of_cards_to_append.append(card_to_add)
                    if not match:
                        print('Card not found: {}'.format(cards))
            deckbuilder.extend_to_deck_of_decoded_cards(list_of_cards_to_append)
    final_image = create_grid_image(deckbuilder.get_deck_of_decoded_cards(), img_name)
    deckbuilder.reset_deck_of_decoded_cards()
    return final_image


def place_header_on_decklist(full_image, header):
    font = cv2.FONT_HERSHEY_TRIPLEX
    font_scale = 4
    color = (255, 255, 255)  # White
    thickness = 5

    x_start = 2400
    y_start = 4750
    y_increment = 200
    for i, line in enumerate(header.split('\n')):
        y = y_start + i * y_increment
        full_image = cv2.putText(full_image, line, (x_start, y), font, font_scale, color, thickness)
    return full_image


def combine_images(main_image, side_image, extra_image, deck_list_name, header):
    combined_pic = cv2.vconcat([main_image, side_image, extra_image])
    final_image_with_header = place_header_on_decklist(combined_pic, header)
    cv2.imwrite('remastered deck lists/' + deck_list_name + '.jpg', final_image_with_header)


class DeckBuilder:
    def __init__(self):
        # self.browser = webdriver.Chrome(
        #     executable_path=r'C:\Users\Richard Le\PycharmProjects\TCGPScraperRemastered\chromedriver.exe')
        self.list_of_decks = get_card_lists('decks/decklists/list_of_decks.yaml')
        self.card_code_list = get_card_lists('decks/decklists/card_code_list.yaml')

        self.current_list = ''
        self.list_name = ''
        self.yaml_data = ''
        self.path = ''
        self.deck_of_decoded_cards = []
        self.alphetical_order = False

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
        if self.alphetical_order:
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
    for current_deck_list in list_of_decks:
        deckbuilder.get_yaml_list_data(current_deck_list, list_of_decks)
        deck_list_name = deckbuilder.get_list_name()
        card_list_in_deck = deckbuilder.get_yaml_data()
        header = deckbuilder.get_header()
        combine_images(generate_image(card_list_in_deck, 'Main'),
                       generate_image(card_list_in_deck, 'Side'),
                       generate_image(card_list_in_deck, 'Extra'),
                       deck_list_name, header)

# To Run PS C:\Users\Richard Le\PycharmProjects\SellerPortalDatabase> python .\decklist_gallery.py

# TODO
# [] plan next ygo coding project
#     [] finish deck lists
#     [] dl wiki images
#     [] decode card list
#       [x] option to overwrite alphabetical ordering
#       [x] categorize img folder - needs to be able to get image from any folder
#       [] output yaml to human readible txt

# 	[x] manual - save wiki pics of all max rarity cards
# 	[x] yaml list of each deck, with option to select different rarities (max rarity default)
#   [x] # Rarity Overwrite logic: space Rarity ID. In logic, we check for space and rarity ID. Get it in card_code_list.yaml
#   [x] yaml deck list, yaml list of basic names with nodes of specific file name (wiki format)
#   [x] data poc script
#   [x] footer text, tag it to the bottom (info, year, creator, event, place, etc)
# 	[x] takes respective pic, resizes it and pastes it into a 4x10 grid. do same with side & extra
# 	[x] save the deck list pic with a name,


# After
#   []	save the deck name & prices into it's own .txt list
# 	- search through min/max/med/mean lists, go to the latest one. retrieve the price and get the full price of the deck
# 	- this should also fix yaml list names to have proper names.
