"""
Card Price Parser - Debug and Test Utilities
Helper functions for testing and debugging the CardPriceParser.
"""

import traceback
from pathlib import Path
from typing import List, Optional
from CardPriceParser import CardPriceParser, CardEntry


class CardPriceDebugger:
    """Debug utilities for the CardPriceParser."""
    
    def __init__(self, parser: CardPriceParser):
        """
        Initialize debugger with a parser instance.
        
        Args:
            parser: CardPriceParser instance to debug
        """
        self.parser = parser
    
    def check_file_exists(self, date_str: str) -> bool:
        """
        Check if a file exists for the given date and print detailed path info.
        
        Args:
            date_str: Date in format "YYYY-MM-DD"
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self.parser.parse_date_to_path(date_str)
        absolute_path = file_path.absolute()
        
        print(f"Looking for file: {file_path}")
        print(f"Absolute path: {absolute_path}")
        print(f"File exists: {file_path.exists()}")
        
        if not file_path.exists():
            self._debug_missing_file(file_path)
        
        return file_path.exists()
    
    def _debug_missing_file(self, file_path: Path):
        """Debug why a file might be missing."""
        parent_dir = file_path.parent
        print(f"Parent directory: {parent_dir}")
        print(f"Parent exists: {parent_dir.exists()}")
        
        if parent_dir.exists():
            print("Files in directory:")
            try:
                for item in parent_dir.iterdir():
                    print(f"  {item.name}")
            except Exception as e:
                print(f"  Error listing directory: {e}")
        else:
            # Check path components
            current_path = self.parser.base_path
            print(f"Checking path components:")
            for part in file_path.relative_to(self.parser.base_path).parts[:-1]:
                current_path = current_path / part
                print(f"  {current_path}: {current_path.exists()}")
    
    def debug_file_contents(self, file_path: Path, max_cards: int = 5):
        """
        Show what cards are being parsed from a file.
        
        Args:
            file_path: Path to the file to debug
            max_cards: Maximum number of cards to display
        """
        print(f"\nDEBUG: Analyzing file {file_path}")
        try:
            cards_data = self.parser.parse_file(file_path)
            print(f"Found {len(cards_data)} cards in file")
            
            if cards_data:
                print(f"First {min(max_cards, len(cards_data))} card keys:")
                for i, (key, data, qty) in enumerate(cards_data[:max_cards]):
                    print(f"  {i + 1}. '{key}' (Qty: {qty})")
            else:
                print("No cards found in file!")
        except Exception as e:
            print(f"Error parsing file: {e}")
            traceback.print_exc()
    
    def compare_dates_debug(self, date1: str, date2: str) -> List[CardEntry]:
        """
        Compare dates with full debug output.
        
        Args:
            date1: First date in YYYY-MM-DD format
            date2: Second date in YYYY-MM-DD format
            
        Returns:
            List of CardEntry objects
        """
        print("\n=== CHECKING FILE PATHS ===")
        file1_exists = self.check_file_exists(date1)
        file2_exists = self.check_file_exists(date2)
        
        if not file1_exists or not file2_exists:
            print("\nOne or both files don't exist. Please check the paths above.")
            return []
        
        file1_path = self.parser.parse_date_to_path(date1)
        file2_path = self.parser.parse_date_to_path(date2)
        
        print("\n=== FILE CONTENTS DEBUG ===")
        self.debug_file_contents(file1_path)
        self.debug_file_contents(file2_path)
        
        print("\n=== STARTING COMPARISON ===")
        try:
            results = self.parser.compare_dates(date1, date2)
            print(f"Comparison completed! Found {len(results)} common cards.")
            return results
        except Exception as e:
            print(f"Error during comparison: {e}")
            traceback.print_exc()
            return []
    
    def test_parsing_logic(self):
        """Test the parsing logic with sample data."""
        sample_lines = [
            "Missing Data for:    Dark Hole LOB 1st",
            "Missing Data for:    Blue-Eyes White Dragon DDS",
            "Missing Data for:    Dark Magician DDS",
            "Sum of Min Listed: $70,609.00",
            "Sum of Max Listed: $104,110.00",
            "Sum of Mean Listed: $83,188.00",
            "Sum of Median Listed: $80,423.00",
            "",
            "Stardust Dragon Ghost 1st [3] - Lightly Played 1st <2>",
            "+------+------+------+--------+",
            "| Min  | Max  | Mean | Median |",
            "+------+------+------+--------+",
            "| 1999 | 2999 | 2499 | 2499.0 |",
            "+------+------+------+--------+",
            "",
            "Black Rose Dragon Ghost 1st [3] - Near Mint 1st <4>",
            "+------+------+------+--------+",
            "| Min  | Max  | Mean | Median |",
            "+------+------+------+--------+",
            "| 1989 | 2899 | 2219 | 1994.5 |",
            "+------+------+------+--------+"
        ]
        
        print("=== TESTING WITH SAMPLE DATA ===")
        cards_found = 0
        
        i = 0
        while i < len(sample_lines):
            line = sample_lines[i].strip()
            
            if not line or line.startswith('Missing Data') or line.startswith('Sum of'):
                i += 1
                continue
            
            # Check for card header
            if all(marker in line for marker in ['[', ']', '<', '>', '-']):
                print(f"\nTesting line {i}: '{line}'")
                try:
                    card_name, condition, quantity = self.parser.extract_card_info(line)
                    print(f"✓ Parsed: name='{card_name}', condition='{condition}', qty={quantity}")
                    
                    # Look for data line
                    for j in range(i + 1, min(i + 10, len(sample_lines))):
                        data_line = sample_lines[j].strip()
                        
                        if (data_line.startswith('|') and data_line.endswith('|') and
                                data_line.count('|') >= 4 and
                                any(char.isdigit() for char in data_line) and
                                not any(word in data_line for word in ['Min', 'Max', '---'])):
                            
                            try:
                                price_data = self.parser.extract_price_data(data_line)
                                print(f"✓ Price data: min=${price_data.min_price}, max=${price_data.max_price}")
                                cards_found += 1
                                break
                            except ValueError as e:
                                print(f"✗ Failed to parse price: {e}")
                
                except Exception as e:
                    print(f"✗ Failed to parse header: {e}")
            
            i += 1
        
        print(f"\n=== TEST RESULT: Found {cards_found} cards ===")
        return cards_found > 0


def debug_comparison(base_path: Optional[str] = None):
    """
    Run a full debug comparison between two dates.
    
    Args:
        base_path: Optional base path for the parser
    """
    parser = CardPriceParser(base_path) if base_path else CardPriceParser()
    debugger = CardPriceDebugger(parser)
    
    # Test parsing logic first
    print("Testing parsing logic...")
    if debugger.test_parsing_logic():
        print("Parsing logic test passed!\n")
    else:
        print("Parsing logic test failed!\n")
    
    # Get dates from user or use defaults
    date1 = input("Enter first date (YYYY-MM-DD) or press Enter for default (2025-01-04): ")
    date1 = date1.strip() or "2025-01-04"
    
    date2 = input("Enter second date (YYYY-MM-DD) or press Enter for default (2025-07-02): ")
    date2 = date2.strip() or "2025-07-02"
    
    # Run debug comparison
    results = debugger.compare_dates_debug(date1, date2)
    
    if results:
        parser.print_comparison_report(results)
        
        export = input("\nExport to CSV? (y/n): ")
        if export.lower() == 'y':
            parser.export_to_csv(results)


if __name__ == "__main__":
    debug_comparison()
