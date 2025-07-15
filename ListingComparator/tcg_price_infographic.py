#!/usr/bin/env python3
"""
TCG Card Price Comparison Infographic Generator

This script reads card price comparison data from CSV files and generates
an infographic showing card images with their price changes.
"""

import os
import csv
import glob
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import numpy as np

# Configuration constants
CARDS_PER_ROW = 10  # Number of cards per row in the infographic
CARD_IMAGE_WIDTH = 300  # Width of each card image in pixels (increased by 50%)
CARD_IMAGE_HEIGHT = 420  # Height of each card image in pixels (increased by 50%)
PADDING = 30  # Padding between cards (increased by 50%)
BACKGROUND_COLOR = "white"  # Background color of the infographic
FONT_SIZE = 21  # Font size for text (increased by 50%)
HEADER_FONT_SIZE = 27  # Font size for headers (increased by 50%)


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

    def __init__(self, base_path: str = "TCGPScraperRemastered/ListingComparator/"):
        self.base_path = Path(base_path)
        self.csv_folder = self.base_path / "card_price_comparisons"
        self.image_folder = Path("TCGPScraperRemastered/decks/decklists/raw_imgs")
        self.cards_data: List[CardData] = []

    def load_csv_data(self, csv_filename: str) -> None:
        """Load card data from CSV file"""
        csv_path = self.csv_folder / csv_filename

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Try to detect delimiter
        with open(csv_path, 'r', encoding='utf-8') as file:
            first_line = file.readline()
            if '\t' in first_line:
                delimiter = '\t'
            else:
                delimiter = ','

        # Read the CSV file
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
                    self.cards_data.append(card)
                except (KeyError, ValueError) as e:
                    print(f"Error processing row {row_num}: {e}")
                    if row_num == 1:  # If first row fails, show the row data
                        print(f"Row data: {row}")
                    continue

    def normalize_string(self, s: str) -> str:
        """Normalize string for comparison by removing special characters and spaces"""
        # Remove special characters and convert to lowercase
        s = re.sub(r'[^a-zA-Z0-9]', '', s.lower())
        return s

    def find_best_image_match(self, card_name: str) -> Optional[str]:
        """Find the best matching image file for a given card name"""
        if not self.image_folder.exists():
            print(f"Image folder not found: {self.image_folder}")
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
        print("Matching images to cards...")
        for i, card in enumerate(self.cards_data):
            image_path = self.find_best_image_match(card.card_name)
            if image_path:
                card.image_path = image_path
                print(f"Matched '{card.card_name}' to '{Path(image_path).name}'")
            else:
                print(f"No match found for '{card.card_name}'")

    def get_arrow_and_color(self, value: float) -> Tuple[str, str]:
        """Get arrow symbol and color based on value change"""
        if value > 0:
            return "↑", "#00AA00"  # Green
        elif value < 0:
            return "↓", "#FF0000"  # Red
        else:
            return "→", "#808080"  # Gray

    def create_card_info_image(self, card: CardData, dates: Tuple[str, str]) -> Image.Image:
        """Create an image for a single card with its price information"""
        # Create a white background for the card info
        info_width = CARD_IMAGE_WIDTH
        info_height = CARD_IMAGE_HEIGHT + 180  # Extra space for price data (increased)
        card_image = Image.new('RGB', (info_width, info_height), 'white')
        draw = ImageDraw.Draw(card_image)

        # Try to load a default font, fall back to PIL default if not available
        try:
            font = ImageFont.truetype("arial.ttf", FONT_SIZE)
            small_font = ImageFont.truetype("arial.ttf", FONT_SIZE - 3)
        except:
            font = ImageFont.load_default()
            small_font = font

        # Load and paste card image if available
        if card.image_path and os.path.exists(card.image_path):
            try:
                img = Image.open(card.image_path)
                img = img.resize((CARD_IMAGE_WIDTH, CARD_IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                card_image.paste(img, (0, 0))
            except Exception as e:
                print(f"Error loading image for {card.card_name}: {e}")
                # Draw placeholder
                draw.rectangle([(0, 0), (CARD_IMAGE_WIDTH, CARD_IMAGE_HEIGHT)],
                               fill='lightgray', outline='black')
                draw.text((10, CARD_IMAGE_HEIGHT // 2), card.card_name, fill='black', font=font)
        else:
            # Draw placeholder
            draw.rectangle([(0, 0), (CARD_IMAGE_WIDTH, CARD_IMAGE_HEIGHT)],
                           fill='lightgray', outline='black')
            draw.text((10, CARD_IMAGE_HEIGHT // 2), card.card_name, fill='black', font=font)

        # Starting position for price data
        y_offset = CARD_IMAGE_HEIGHT + 10
        # Adjusted column positions for better spacing
        x_positions = [10, 70, 130, 190, 260]  # Increased spacing between columns

        # Price data rows
        price_data = [
            ("Min", card.date1_min, card.date2_min, card.min_diff, card.min_percent),
            ("Max", card.date1_max, card.date2_max, card.max_diff, card.max_percent),
            ("Mean", card.date1_mean, card.date2_mean, card.mean_diff, card.mean_percent),
            ("Med", card.date1_median, card.date2_median, card.median_diff, card.median_percent)
        ]

        for i, (label, date1_val, date2_val, diff, percent) in enumerate(price_data):
            y_pos = y_offset + i * 40  # Increased vertical spacing

            # Date 1 value
            draw.text((x_positions[0], y_pos), f"${date1_val:.0f}", fill='black', font=font)

            # Date 2 value
            draw.text((x_positions[1], y_pos), f"${date2_val:.0f}", fill='black', font=font)

            # Get color based on change
            arrow, color = self.get_arrow_and_color(percent)

            # Difference with color and plus sign for positive values
            diff_text = f"+${diff:.0f}" if diff > 0 else f"${diff:.0f}"
            draw.text((x_positions[2], y_pos), diff_text, fill=color, font=font)

            # Percentage with color and plus sign for positive values
            percent_text = f"+{percent:.1f}%" if percent > 0 else f"{percent:.1f}%"
            draw.text((x_positions[3], y_pos), percent_text, fill=color, font=font)

            # Arrow
            draw.text((x_positions[4], y_pos), arrow, fill=color, font=font)

        return card_image

    def create_infographic(self, output_filename: str = "card_price_infographic.jpg",
                           cards_per_row: int = CARDS_PER_ROW) -> None:
        """Create the full infographic with all cards"""
        if not self.cards_data:
            print("No card data loaded!")
            return

        # Get dates from first card (assuming all cards have same dates)
        dates = (self.cards_data[0].date1, self.cards_data[0].date2)

        # Calculate grid dimensions
        num_cards = len(self.cards_data)
        num_rows = (num_cards + cards_per_row - 1) // cards_per_row

        # Calculate image dimensions
        card_total_width = CARD_IMAGE_WIDTH + PADDING
        card_total_height = CARD_IMAGE_HEIGHT + 180 + PADDING  # Updated to match new height

        img_width = cards_per_row * card_total_width + PADDING
        img_height = num_rows * card_total_height + PADDING + 75  # Extra space for header

        # Create the main image
        infographic = Image.new('RGB', (img_width, img_height), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(infographic)

        # Add header with dates
        try:
            header_font = ImageFont.truetype("arial.ttf", HEADER_FONT_SIZE)
        except:
            header_font = ImageFont.load_default()

        header_text = f"Card Price Comparison: {dates[0]} vs {dates[1]}"
        draw.text((PADDING, 10), header_text, fill='black', font=header_font)

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
        output_path = self.base_path / output_filename
        infographic.save(output_path, 'JPEG', quality=95)
        print(f"Infographic saved to: {output_path}")


def main():
    """Main function to run the infographic generator"""
    import sys

    # Use absolute paths for Windows
    base_path = r"C:\Users\Richard Le\PycharmProjects\TCGPScraperRemastered\ListingComparator"
    csv_path = r"C:\Users\Richard Le\PycharmProjects\TCGPScraperRemastered\ListingComparator\card_price_comparisons\comparison_2025-01-04_vs_2025-07-02.csv"
    image_base_path = r"C:\Users\Richard Le\PycharmProjects\TCGPScraperRemastered\decks\decklists\raw_imgs"

    # Initialize the generator with absolute base path
    generator = CardPriceInfographic(base_path=base_path)

    # Override the image folder path
    generator.image_folder = Path(image_base_path)

    # Check if CSV exists
    if not Path(csv_path).exists():
        print(f"CSV file not found at: {csv_path}")
        print(f"Current working directory: {os.getcwd()}")
        return

    # Load the CSV data using just the filename
    csv_filename = Path(csv_path).name
    print(f"Loading data from: {csv_filename}")

    # Load the CSV data
    generator.load_csv_data(csv_filename)
    print(f"Loaded {len(generator.cards_data)} cards")

    # Match images to cards
    generator.match_images_to_cards()

    # Create the infographic
    generator.create_infographic(
        output_filename="card_price_infographic.jpg",
        cards_per_row=CARDS_PER_ROW  # Can be modified here
    )


if __name__ == "__main__":
    main()
