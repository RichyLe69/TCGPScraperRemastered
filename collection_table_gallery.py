import os
import cv2
import numpy as np
from utils import get_card_lists

# Configs
overlay_percentage = 0.33  # How much of the card width to show (0.33 = 1/3 width visible)
cards_per_row = 10
number_of_rows = 4
card_width = 450
card_height = 657
output_directory = 'TableGallery/'


def get_decoded_card_filename(card_name, card_code_list):
    """Get the decoded filename from card_code_list"""
    # First try exact match
    for decode in card_code_list:
        if card_name == decode:
            # Return the first entry (max rarity) filename
            return card_code_list[decode][0]

    # If no exact match and card has dots, try matching without dots
    if '.' in card_name:
        base_name = card_name.rstrip('.')
        for decode in card_code_list:
            if base_name == decode:
                # Return the first entry (max rarity) filename
                return card_code_list[decode][0]

    print(f'Card missing from card_code_list.yaml: {card_name}')
    return None


def get_card_image_paths(list_of_cards, card_code_list):
    """Get full paths for all card images in the list"""
    card_image_paths = []
    path_to_card_images = "decks/decklists/raw_imgs"

    for card_name in list_of_cards:
        # Get decoded filename from card_code_list
        decoded_filename = get_decoded_card_filename(card_name, card_code_list)
        if not decoded_filename:
            continue

        card_filename = decoded_filename + '.jpg'
        card_found = False

        # Try .jpg first
        for dirpath, dirnames, filenames in os.walk(path_to_card_images):
            if card_filename in filenames:
                card_image_paths.append(os.path.join(dirpath, card_filename))
                card_found = True
                break

        # Try .png if .jpg not found
        if not card_found:
            print(f'Trying .png. Image Not Found: {card_filename}')
            card_filename = decoded_filename + '.png'
            for dirpath, dirnames, filenames in os.walk(path_to_card_images):
                if card_filename in filenames:
                    card_image_paths.append(os.path.join(dirpath, card_filename))
                    card_found = True
                    break

        if not card_found:
            print(f'Image Not Found: {decoded_filename}')

    return card_image_paths


def expand_card_list_with_quantities(card_dict, card_code_list):
    """Convert card dict with quantities to flat list, handling rarity overrides"""
    expanded_list = []
    for card_name, quantity in card_dict.items():
        if isinstance(quantity, str):  # Handle rarity strings like "3 ScR"
            qty, rarity = quantity.split(' ', 1)
            qty = int(qty)
            # Handle different rarity
            rarity_code = '-' + rarity + '-'
            decoded_card = None

            # First check for exact match
            for decode in card_code_list:
                if card_name == decode:
                    for variant in card_code_list[decode]:
                        if rarity_code in variant:
                            decoded_card = variant
                            break
                    break

            # If no exact match and card has dots, try base name
            if not decoded_card and '.' in card_name:
                base_name = card_name.rstrip('.')
                for decode in card_code_list:
                    if base_name == decode:
                        for variant in card_code_list[decode]:
                            if rarity_code in variant:
                                decoded_card = variant
                                break
                        break

            if decoded_card:
                for _ in range(qty):
                    expanded_list.append((card_name, decoded_card))
            else:
                # Use max rarity if specific rarity not found
                for _ in range(qty):
                    expanded_list.append((card_name, None))
        else:
            qty = int(quantity)
            for _ in range(qty):
                expanded_list.append((card_name, None))

    return expanded_list


def get_card_image_paths_with_override(card_list, card_code_list):
    """Get full paths for all card images, handling rarity overrides"""
    card_image_paths = []
    path_to_card_images = "decks/decklists/raw_imgs"

    for item in card_list:
        if isinstance(item, tuple):
            card_name, specific_decode = item
            decoded_filename = specific_decode if specific_decode else get_decoded_card_filename(card_name,
                                                                                                 card_code_list)
        else:
            card_name = item
            decoded_filename = get_decoded_card_filename(card_name, card_code_list)

        if not decoded_filename:
            continue

        card_filename = decoded_filename + '.jpg'
        card_found = False

        # Try .jpg first
        for dirpath, dirnames, filenames in os.walk(path_to_card_images):
            if card_filename in filenames:
                card_image_paths.append(os.path.join(dirpath, card_filename))
                card_found = True
                break

        # Try .png if .jpg not found
        if not card_found:
            print(f'Trying .png. Image Not Found: {card_filename}')
            card_filename = decoded_filename + '.png'
            for dirpath, dirnames, filenames in os.walk(path_to_card_images):
                if card_filename in filenames:
                    card_image_paths.append(os.path.join(dirpath, card_filename))
                    card_found = True
                    break

        if not card_found:
            print(f'Image Not Found: {decoded_filename}')

    return card_image_paths


def create_table_gallery(card_list, card_code_list, rows=None, cols=None, overlap=None):
    """Create gallery image with overlapping cards"""
    # Use provided values or defaults
    rows = rows or number_of_rows
    cols = cols or cards_per_row
    overlap = overlap or overlay_percentage

    # Calculate canvas dimensions
    visible_width = int(card_width * overlap)
    canvas_width = visible_width * (cols - 1) + card_width
    canvas_height = rows * card_height

    # Create blank canvas
    final_image = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    # Get image paths
    image_paths = get_card_image_paths_with_override(card_list, card_code_list)

    # Place cards on canvas
    for i in range(min(len(image_paths), rows * cols)):
        try:
            img = cv2.imread(image_paths[i])
            if img is None:
                continue
            img = cv2.resize(img, (card_width, card_height))

            # Calculate position
            row = i // cols
            col = i % cols

            y_start = row * card_height
            y_end = y_start + card_height
            x_start = col * visible_width
            x_end = x_start + card_width

            # Place card on canvas
            final_image[y_start:y_end, x_start:x_end, :] = img

        except Exception as e:
            print(f"Error processing card {i}: {e}")

    return final_image


def add_header_to_image(image, header_text):
    """Add header text to top of image"""
    font = cv2.FONT_HERSHEY_TRIPLEX
    font_scale = 3
    color = (255, 255, 255)
    thickness = 4

    height, width = image.shape[:2]
    header_height = 150

    # Create canvas with extra space for header
    canvas = np.zeros((height + header_height, width, 3), dtype=np.uint8)
    canvas[header_height:, :] = image

    # Add text
    text_size = cv2.getTextSize(header_text, font, font_scale, thickness)[0]
    text_x = (width - text_size[0]) // 2
    text_y = header_height // 2 + text_size[1] // 2

    canvas = cv2.putText(canvas, header_text, (text_x, text_y), font, font_scale, color, thickness)

    return canvas


def generate_collection_table(yaml_file, output_name=None, custom_rows=None, custom_cols=None, custom_overlap=None):
    """Main function to generate collection table gallery"""
    # Load card code list for decoding
    card_code_list = get_card_lists('decks/decklists/card_code_list.yaml')

    # Load card list from yaml
    card_data = get_card_lists(yaml_file)

    # Get header if exists
    header = card_data.get('Header', '')

    # Combine all cards from different sections
    all_cards = []
    for section in ['Monsters', 'Spells', 'Traps', 'Extra', 'Side']:
        if section in card_data:
            expanded_cards = expand_card_list_with_quantities(card_data[section], card_code_list)
            all_cards.extend(expanded_cards)

    if not all_cards:
        print("No cards found in yaml file")
        return

    # Create gallery
    gallery_image = create_table_gallery(all_cards, card_code_list, custom_rows, custom_cols, custom_overlap)

    # Add header if provided
    if header:
        gallery_image = add_header_to_image(gallery_image, header)

    # Save image
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_filename = output_name or yaml_file.split('/')[-1].replace('.yaml', '')
    output_path = os.path.join(output_directory, f'{output_filename}_table.jpg')

    cv2.imwrite(output_path, gallery_image)
    print(f"Table gallery saved to: {output_path}")

    return gallery_image


def generate_custom_list_table(card_list, output_name, header_text=None, custom_rows=None, custom_cols=None,
                               custom_overlap=None):
    """Generate table gallery from a simple list of cards"""
    if not card_list:
        print("Card list is empty")
        return

    # Load card code list for decoding
    card_code_list = get_card_lists('decks/decklists/card_code_list.yaml')

    # Convert simple list to format expected by create_table_gallery
    formatted_list = [(card, None) for card in card_list]

    # Create gallery
    gallery_image = create_table_gallery(formatted_list, card_code_list, custom_rows, custom_cols, custom_overlap)

    # Add header if provided
    if header_text:
        gallery_image = add_header_to_image(gallery_image, header_text)

    # Save image
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_path = os.path.join(output_directory, f'{output_name}_table.jpg')
    cv2.imwrite(output_path, gallery_image)
    print(f"Table gallery saved to: {output_path}")

    return gallery_image


if __name__ == '__main__':
    # Example 2: Generate with custom parameters
    generate_collection_table('decks/decklists/collection-max-rarity.yaml',
                              output_name='collection-max-rarity',
                              custom_rows=15,
                              custom_cols=30,
                              custom_overlap=0.65)
