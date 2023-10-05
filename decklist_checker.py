from utils import get_card_lists
from CardList import CardList


def convert_decklist_yaml_to_clean_dictionary(decklist_yaml_data):
    converted_data = {
        'Header': decklist_yaml_data['Header'],
        'Monsters': {
            **decklist_yaml_data['Monsters'],
            **decklist_yaml_data['Spells'],
            **decklist_yaml_data['Traps'],
            # **decklist_yaml_data['Side'], # Omit the Side Deck
            # **decklist_yaml_data['Extra'] # Omit the Extra deck
        }
    }
    return converted_data


class Decklist_Checker:
    def __init__(self):
        self.list_of_decks = get_card_lists('decks/decklists/list_of_decks.yaml')
        self.list_of_binders = get_card_lists('decks/decklists/list_of_binders.yaml')

    def get_yaml_list_data(self, current_deck_list):
        self.current_list = CardList(current_deck_list['path'], current_deck_list)
        self.list_name = (self.current_list.get_list_name())
        self.yaml_data = (self.current_list.get_yaml_data())
        self.path = (self.current_list.get_path())

    def get_yaml_list_data_binders(self, current_deck_list, full_card_lists):
        self.current_list = CardList(full_card_lists[current_deck_list]['path'], current_deck_list)
        self.list_name = (self.current_list.get_list_name())
        self.yaml_data = (self.current_list.get_yaml_data())
        self.path = (self.current_list.get_path())

    def get_list_name(self):
        return self.list_name

    def get_list_of_binders(self):
        return self.list_of_binders

    def get_yaml_data(self):
        return self.yaml_data


if __name__ == '__main__':
    decklist_checker = Decklist_Checker()
    list_of_binders = decklist_checker.get_list_of_binders()

    list_of_decks = ['2009-twilight', '2009-twilight']
    # list_of_decks = ['2009-teledad', '2009-teledad']
    # list_of_decks = ['2009-twilight', '2009-teledad']
    # list_of_decks = ['2011-tenguplant', '2011-tenguplant']
    # list_of_decks = ['2012-dinorabbit', '2012-dinorabbit']
    # list_of_decks = ['2011-tenguplant', '2012-dinorabbit']
    full_binder_card_list = {}

    # getting the binder list json yaml
    for current_binder_list in list_of_binders:
        decklist_checker.get_yaml_list_data_binders(current_binder_list, list_of_binders)
        binder_list_name = decklist_checker.get_list_name()
        card_list_in_deck = decklist_checker.get_yaml_data()

        binder_card_list = (card_list_in_deck['Monsters'])
        full_binder_card_list.update(binder_card_list)

    # getting the deck list json yaml
    for deck in list_of_decks:
        current_deck_list = (decklist_checker.list_of_decks[deck])
        decklist_checker.get_yaml_list_data(current_deck_list)
        deck_list_name = decklist_checker.get_list_name()
        card_list_in_deck = decklist_checker.get_yaml_data()

        clean_decklist_data = (convert_decklist_yaml_to_clean_dictionary(card_list_in_deck))
        clean_decklist_data = (clean_decklist_data['Monsters'])
        # start subtracting from full binder card list

        for item, quantity in clean_decklist_data.items():
            if item in full_binder_card_list and full_binder_card_list[item] >= quantity:
                full_binder_card_list[item] -= quantity
            else:
                print(
                    f"Not enough copies of {item}. Available: {full_binder_card_list.get(item, 0)}, Requested: {quantity}")
