#!/usr/bin/env python3
"""
TCG Card Price Comparison Infographic Generator

This script reads card price comparison data from CSV files and generates
an infographic showing card images with their price changes.
"""

import os
import csv
import glob
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import numpy as np

# Configuration constants
CARDS_PER_ROW = 10  # Number of cards per row in the infographic
CARD_IMAGE_WIDTH = 300  # Width of each card image in pixels
CARD_IMAGE_HEIGHT = 420  # Height of each card image in pixels
PADDING = 30  # Padding between cards
BACKGROUND_COLOR = "white"  # Background color of the infographic
FONT_SIZE = 18  # Font size for text
HEADER_FONT_SIZE = 27  # Font size for headers


@dataclass
class CardData:
    """Data structure for holding card information"""
    card_name: str
    condition: str
    date1: str
    date2: str
    date1_min: float
    date1_max: float
    date1_mean: float
    date1_median: float
    date2_min: float
    date2_max: float
    date2_mean: float
    date2_median: float
    min_diff: float
    max_diff: float
    mean_diff: float
    median_diff: float
    min_percent: float
    max_percent: float
    mean_percent: float
    median_percent: float
    image_path: Optional[str] = None


class CardPriceInfographic:
    """Main class for generating card price comparison infographic"""

    def __init__(self, project_root: str = None):
        """Initialize with project root path"""
        self.project_root = self._find_project_root(project_root)
        self.base_path = self.project_root / "ListingComparator"
        self.csv_folder = self.base_path / "card_price_comparisons"
        self.image_folder = self.project_root / "decks" / "decklists" / "raw_imgs"
        self.output_folder = self.base_path / "infographics"
        self.cards_data: List[CardData] = []
        self.card_image_mappings: Dict[str, str] = {}

        # Create output folder if it doesn't exist
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def _find_project_root(self, project_root: str = None) -> Path:
        """Find the project root directory"""
        if project_root:
            return Path(project_root)

        # Start from current directory and look for TCGPScraperRemastered
        current_dir = Path.cwd()

        # Check if we're already in the project directory
        if current_dir.name == "TCGPScraperRemastered":
            return current_dir

        # Look for TCGPScraperRemastered in current directory
        tcg_dir = current_dir / "TCGPScraperRemastered"
        if tcg_dir.exists():
            return tcg_dir

        # Look up the directory tree
        for parent in current_dir.parents:
            tcg_dir = parent / "TCGPScraperRemastered"
            if tcg_dir.exists():
                return tcg_dir

        # If not found, assume current directory is the project root
        print(f"Warning: Could not find TCGPScraperRemastered directory. Using current directory: {current_dir}")
        return current_dir

    def setup_directories(self) -> bool:
        """Verify and create necessary directories"""
        try:
            # Create output directory
            self.output_folder.mkdir(parents=True, exist_ok=True)

            # Check if required directories exist
            if not self.csv_folder.exists():
                print(f"Warning: CSV folder not found at {self.csv_folder}")
                return False

            if not self.image_folder.exists():
                print(f"Warning: Image folder not found at {self.image_folder}")
                print("Image matching will be skipped")

            return True

        except Exception as e:
            print(f"Error setting up directories: {e}")
            return False

    def load_image_mappings(self) -> None:
        """Load hard-coded card-to-image mappings from YAML file"""
        yaml_path = self.base_path / "card_image_mappings.yaml"

        if yaml_path.exists():
            try:
                with open(yaml_path, 'r', encoding='utf-8') as file:
                    self.card_image_mappings = yaml.load(file, Loader=yaml.SafeLoader) or {}
                print(f"Loaded {len(self.card_image_mappings)} hard-coded image mappings")
            except Exception as e:
                print(f"Error loading image mappings: {e}")
        else:
            self._create_sample_yaml(yaml_path)

    def _create_sample_yaml(self, yaml_path: Path) -> None:
        """Create a sample YAML file for image mappings"""
        sample_mappings = {
            "Stardust Dragon Ghost 1st": "StardustDragon-TDGS-EN-GR-1E.jpg",
            "Black Rose Dragon Ghost 1st": "BlackRoseDragon-CSOC-EN-GR-1E.jpg",
            # Add more mappings as needed
        }
        try:
            with open(yaml_path, 'w', encoding='utf-8') as file:
                yaml.dump(sample_mappings, file, default_flow_style=False)
            print(f"Created sample card_image_mappings.yaml at {yaml_path}")
        except Exception as e:
            print(f"Error creating sample YAML: {e}")

    def get_available_csv_files(self) -> List[str]:
        """Get list of available CSV files in the comparisons folder"""
        if not self.csv_folder.exists():
            return []

        csv_files = []
        for file_path in self.csv_folder.glob("*.csv"):
            csv_files.append(file_path.name)

        return sorted(csv_files)

    def select_csv_file(self) -> Optional[str]:
        """Prompt user to select a CSV file from available options"""
        csv_files = self.get_available_csv_files()

        if not csv_files:
            print(f"No CSV files found in {self.csv_folder}")
            return None

        print("\nAvailable CSV files:")
        for i, filename in enumerate(csv_files, 1):
            print(f"{i}. {filename}")

        while True:
            try:
                choice = input(f"\nSelect a CSV file (1-{len(csv_files)}): ").strip()
                if choice.lower() in ['q', 'quit', 'exit']:
                    return None

                choice_num = int(choice)
                if 1 <= choice_num <= len(csv_files):
                    selected_file = csv_files[choice_num - 1]
                    print(f"Selected: {selected_file}")
                    return selected_file
                else:
                    print(f"Please enter a number between 1 and {len(csv_files)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\nOperation cancelled")
                return None

    def load_csv_data(self, csv_filename: str) -> bool:
        """Load card data from CSV file"""
        csv_path = self.csv_folder / csv_filename

        if not csv_path.exists():
            print(f"CSV file not found: {csv_path}")
            return False

        try:
            delimiter = self._detect_csv_delimiter(csv_path)
            self.cards_data = self._parse_csv_file(csv_path, delimiter)
            print(f"Successfully loaded {len(self.cards_data)} cards from {csv_filename}")
            return True
        except Exception as e:
            print(f"Error loading CSV data: {e}")
            return False

    def _detect_csv_delimiter(self, csv_path: Path) -> str:
        """Detect the delimiter used in the CSV file"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                first_line = file.readline()
                if '\t' in first_line:
                    return '\t'
                else:
                    return ','
        except Exception as e:
            print(f"Error detecting delimiter: {e}")
            return ','

    def _parse_csv_file(self, csv_path: Path, delimiter: str) -> List[CardData]:
        """Parse CSV file and return list of CardData objects"""
        cards_data = []

        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=delimiter)

            # Print column names for debugging
            print(f"CSV columns found: {reader.fieldnames}")

            for row_num, row in enumerate(reader, 1):
                try:
                    card = CardData(
                        card_name=row['card_name'].strip(),
                        condition=row['condition'].strip(),
                        date1=row['date1'].strip(),
                        date2=row['date2'].strip(),
                        date1_min=float(row['date1_min']),
                        date1_max=float(row['date1_max']),
                        date1_mean=float(row['date1_mean']),
                        date1_median=float(row['date1_median']),
                        date2_min=float(row['date2_min']),
                        date2_max=float(row['date2_max']),
                        date2_mean=float(row['date2_mean']),
                        date2_median=float(row['date2_median']),
                        min_diff=float(row['min_diff']),
                        max_diff=float(row['max_diff']),
                        mean_diff=float(row['mean_diff']),
                        median_diff=float(row['median_diff']),
                        min_percent=float(row['min_percent']),
                        max_percent=float(row['max_percent']),
                        mean_percent=float(row['mean_percent']),
                        median_percent=float(row['median_percent'])
                    )
                    cards_data.append(card)
                except (KeyError, ValueError) as e:
                    print(f"Error processing row {row_num}: {e}")
                    if row_num == 1:  # If first row fails, show the row data
                        print(f"Row data: {row}")
                    continue

        return cards_data

    def normalize_string(self, s: str) -> str:
        """Normalize string for comparison by removing special characters and spaces"""
        # Remove special characters and convert to lowercase
        s = re.sub(r'[^a-zA-Z0-9]', '', s.lower())
        return s

    def find_best_image_match(self, card_name: str) -> Optional[str]:
        """Find the best matching image file for a given card name"""
        # First check if we have a hard-coded mapping
        if card_name in self.card_image_mappings:
            mapped_filename = self.card_image_mappings[card_name]
            # Search for this exact filename in all subdirectories
            for image_path in self.image_folder.glob(f"**/{mapped_filename}"):
                print(f"Using hard-coded mapping for '{card_name}' -> '{mapped_filename}'")
                return str(image_path)
            print(f"Warning: Hard-coded image '{mapped_filename}' not found for '{card_name}'")

        if not self.image_folder.exists():
            return None

        # Normalize the card name for comparison
        normalized_card_name = self.normalize_string(card_name)

        best_match = None
        best_score = 0

        # Search through all subdirectories
        for image_path in self.image_folder.glob("**/*.jpg"):
            # Get just the filename without extension
            filename = image_path.stem
            normalized_filename = self.normalize_string(filename)

            # Calculate similarity score
            score = SequenceMatcher(None, normalized_card_name, normalized_filename).ratio()

            # Also check if all words from card name are in filename
            card_words = card_name.lower().split()
            filename_lower = filename.lower()
            word_match_score = sum(1 for word in card_words if word in filename_lower) / len(card_words)

            # Combined score
            combined_score = (score + word_match_score) / 2

            if combined_score > best_score:
                best_score = combined_score
                best_match = str(image_path)

        # Only return if we have a reasonably good match
        if best_score > 0.5:
            return best_match
        return None

    def match_images_to_cards(self) -> None:
        """Match image files to each card in the dataset"""
        if not self.image_folder.exists():
            print("Image folder not found, skipping image matching")
            return

        print("Matching images to cards...")
        matched_count = 0

        for card in self.cards_data:
            image_path = self.find_best_image_match(card.card_name)
            if image_path:
                card.image_path = image_path
                print(f"Matched '{card.card_name}' to '{Path(image_path).name}'")
                matched_count += 1
            else:
                print(f"No match found for '{card.card_name}'")

        print(f"Successfully matched {matched_count} out of {len(self.cards_data)} cards")

    def get_price_change_indicators(self, value: float) -> Tuple[str, str]:
        """Get arrow symbol and color based on value change"""
        if value > 0:
            return "↑", "#00AA00"  # Green
        elif value < 0:
            return "↓", "#FF0000"  # Red
        else:
            return "→", "#808080"  # Gray

    def get_text_indicators(self, value: float) -> str:
        """Get text representation of arrow for fonts that don't support Unicode"""
        if value > 0:
            return "UP"
        elif value < 0:
            return "DOWN"
        else:
            return "SAME"

    def load_fonts(self) -> Tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, bool]:
        """Load fonts with fallback options"""
        font = None
        mono_font = None
        use_unicode_arrows = True

        try:
            # Try to load TrueType fonts
            font = ImageFont.truetype("arial.ttf", FONT_SIZE)
            try:
                mono_font = ImageFont.truetype("consolas.ttf", FONT_SIZE)
            except:
                try:
                    mono_font = ImageFont.truetype("courier.ttf", FONT_SIZE)
                except:
                    mono_font = font
        except:
            # Fall back to default font
            font = ImageFont.load_default()
            mono_font = font
            use_unicode_arrows = False  # Default font doesn't support Unicode arrows

        return font, mono_font, use_unicode_arrows

    def create_card_placeholder(self, card_name: str, draw: ImageDraw.Draw, font: ImageFont.FreeTypeFont) -> None:
        """Create a placeholder image for cards without images"""
        draw.rectangle([(0, 0), (CARD_IMAGE_WIDTH, CARD_IMAGE_HEIGHT)],
                       fill='lightgray', outline='black')

        # Wrap text for long card names
        words = card_name.split()
        y_text = CARD_IMAGE_HEIGHT // 2 - 20
        for i in range(0, len(words), 3):
            line = ' '.join(words[i:i + 3])
            draw.text((10, y_text), line, fill='black', font=font)
            y_text += 25

    def create_card_info_image(self, card: CardData, dates: Tuple[str, str]) -> Image.Image:
        """Create an image for a single card with its price information"""
        # Create a white background for the card info
        info_width = CARD_IMAGE_WIDTH
        info_height = CARD_IMAGE_HEIGHT + 180  # Extra space for price data
        card_image = Image.new('RGB', (info_width, info_height), 'white')
        draw = ImageDraw.Draw(card_image)

        # Load fonts
        font, mono_font, use_unicode_arrows = self.load_fonts()

        # Load and paste card image if available
        if card.image_path and os.path.exists(card.image_path):
            try:
                img = Image.open(card.image_path)
                img = img.resize((CARD_IMAGE_WIDTH, CARD_IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                card_image.paste(img, (0, 0))
            except Exception as e:
                print(f"Error loading image for {card.card_name}: {e}")
                self.create_card_placeholder(card.card_name, draw, font)
        else:
            self.create_card_placeholder(card.card_name, draw, font)

        # Add price information
        self._add_price_info_to_card(card, draw, mono_font, font, use_unicode_arrows)

        return card_image

    def _add_price_info_to_card(self, card: CardData, draw: ImageDraw.Draw,
                                mono_font: ImageFont.FreeTypeFont, font: ImageFont.FreeTypeFont,
                                use_unicode_arrows: bool) -> None:
        """Add price information to the card image"""
        # Starting position for price data
        y_offset = CARD_IMAGE_HEIGHT + 10
        x_positions = [5, 80, 150, 220, 280]  # Column positions

        # Price data rows
        price_data = [
            ("Min", card.date1_min, card.date2_min, card.min_diff, card.min_percent),
            ("Max", card.date1_max, card.date2_max, card.max_diff, card.max_percent),
            ("Mean", card.date1_mean, card.date2_mean, card.mean_diff, card.mean_percent),
            ("Med", card.date1_median, card.date2_median, card.median_diff, card.median_percent)
        ]

        for i, (label, date1_val, date2_val, diff, percent) in enumerate(price_data):
            y_pos = y_offset + i * 40

            # Date 1 value with comma formatting
            date1_text = f"${date1_val:,.0f}"
            draw.text((x_positions[0], y_pos), date1_text, fill='black', font=mono_font)

            # Date 2 value with comma formatting
            date2_text = f"${date2_val:,.0f}"
            draw.text((x_positions[1], y_pos), date2_text, fill='black', font=mono_font)

            # Get color based on change
            arrow, color = self.get_price_change_indicators(percent)

            # Difference with color and plus sign for positive values
            diff_text = f"+${diff:,.0f}" if diff > 0 else f"${diff:,.0f}"
            draw.text((x_positions[2], y_pos), diff_text, fill=color, font=mono_font)

            # Percentage with color and plus sign for positive values
            percent_text = f"+{percent:.1f}%" if percent > 0 else f"{percent:.1f}%"
            draw.text((x_positions[3], y_pos), percent_text, fill=color, font=mono_font)

            # Arrow or text indicator
            if use_unicode_arrows:
                try:
                    draw.text((x_positions[4], y_pos), arrow, fill=color, font=font)
                except:
                    # Fallback to text if Unicode fails
                    arrow_text = self.get_text_indicators(percent)
                    draw.text((x_positions[4], y_pos), arrow_text, fill=color, font=font)
            else:
                # Use text indicators for default font
                arrow_text = self.get_text_indicators(percent)
                draw.text((x_positions[4], y_pos), arrow_text, fill=color, font=font)

    def calculate_infographic_dimensions(self, cards_per_row: int) -> Tuple[int, int, int, int]:
        """Calculate the dimensions for the infographic"""
        num_cards = len(self.cards_data)
        num_rows = (num_cards + cards_per_row - 1) // cards_per_row

        # Calculate image dimensions
        card_total_width = CARD_IMAGE_WIDTH + PADDING
        card_total_height = CARD_IMAGE_HEIGHT + 180 + PADDING

        img_width = cards_per_row * card_total_width + PADDING
        img_height = num_rows * card_total_height + PADDING + 75  # Extra space for header

        return img_width, img_height, card_total_width, card_total_height

    def create_infographic_header(self, draw: ImageDraw.Draw, dates: Tuple[str, str]) -> None:
        """Create the header for the infographic"""
        try:
            header_font = ImageFont.truetype("arial.ttf", HEADER_FONT_SIZE)
        except:
            header_font = ImageFont.load_default()

        header_text = f"Card Price Comparison: {dates[0]} vs {dates[1]}"
        draw.text((PADDING, 10), header_text, fill='black', font=header_font)

    def create_infographic(self, output_filename: str = None,
                           cards_per_row: int = CARDS_PER_ROW) -> bool:
        """Create the full infographic with all cards"""
        if not self.cards_data:
            print("No card data loaded!")
            return False

        # Generate filename with timestamp if not provided
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_filename = f"card_price_infographic_{timestamp}.jpg"

        # Get dates from first card (assuming all cards have same dates)
        dates = (self.cards_data[0].date1, self.cards_data[0].date2)

        # Calculate dimensions
        img_width, img_height, card_total_width, card_total_height = self.calculate_infographic_dimensions(
            cards_per_row)

        # Create the main image
        infographic = Image.new('RGB', (img_width, img_height), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(infographic)

        # Add header
        self.create_infographic_header(draw, dates)

        # Add each card to the infographic
        for i, card in enumerate(self.cards_data):
            row = i // cards_per_row
            col = i % cards_per_row

            x_pos = col * card_total_width + PADDING
            y_pos = row * card_total_height + PADDING + 50

            # Create card info image
            card_img = self.create_card_info_image(card, dates)

            # Paste onto main infographic
            infographic.paste(card_img, (x_pos, y_pos))

        # Save the infographic
        return self._save_infographic(infographic, output_filename)

    def _save_infographic(self, infographic: Image.Image, output_filename: str) -> bool:
        """Save the infographic to file"""
        try:
            output_path = self.output_folder / output_filename
            infographic.save(output_path, 'JPEG', quality=95)
            print(f"Infographic saved to: {output_path}")
            print(f"Full path: {output_path.absolute()}")
            return True
        except Exception as e:
            print(f"Error saving infographic: {e}")
            return False


def main():
    """Main function to run the infographic generator"""
    print("TCG Card Price Comparison Infographic Generator")
    print("=" * 50)

    # Initialize the generator
    generator = CardPriceInfographic()

    # Setup directories
    if not generator.setup_directories():
        print("Failed to setup directories. Exiting.")
        return

    # Load image mappings
    generator.load_image_mappings()

    # Select CSV file
    csv_filename = generator.select_csv_file()
    if not csv_filename:
        print("No CSV file selected. Exiting.")
        return

    # Load CSV data
    if not generator.load_csv_data(csv_filename):
        print("Failed to load CSV data. Exiting.")
        return

    # Match images to cards
    generator.match_images_to_cards()

    # Create the infographic
    if generator.create_infographic(cards_per_row=CARDS_PER_ROW):
        print("Infographic created successfully!")
    else:
        print("Failed to create infographic.")


if __name__ == "__main__":
    main()