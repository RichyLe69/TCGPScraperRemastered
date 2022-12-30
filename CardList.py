import yaml


class CardList:

    def __init__(self, path, list_name):
        with open(path, 'r') as stream:
            try:
                yaml_data = yaml.safe_load(stream)
                card_list = list()
                for cards in yaml_data:
                    card_list.append(cards)
            except yaml.YAMLError as exc:
                print(exc)
        self.yaml_data = yaml_data
        self.card_list = card_list
        self.path = path
        self.list_name = list_name

    def get_card_list(self):
        return self.card_list

    def get_yaml_data(self):
        return self.yaml_data

    def get_path(self):
        return self.path

    def get_list_name(self):
        return self.list_name
