"""
Card Price Parser - Production Version
Analyzes and compares Yu-Gi-Oh card prices across different dates.
"""

import re
import csv
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path


@dataclass
class CardPriceData:
    """Data class to store card price information."""
    min_price: float
    max_price: float
    mean_price: float
    median_price: float
    quantity: int


@dataclass
class CardEntry:
    """Data class to store complete card entry information."""
    name: str
    condition: str
    date1_data: CardPriceData
    date2_data: CardPriceData
    min_diff: float
    max_diff: float
    mean_diff: float
    median_diff: float
    min_percent: float
    max_percent: float
    mean_percent: float
    median_percent: float
    quantity_diff: int
    date1: str
    date2: str


class CardPriceParser:
    """Parser for Yu-Gi-Oh card price data files."""

    def __init__(self, base_path: str = "../full_listings"):
        """
        Initialize the parser with the base directory path.

        Args:
            base_path: Base directory containing the price data files
        """
        self.base_path = Path(base_path)
    
    def parse_date_to_path(self, date_str: str) -> Path:
        """
        Convert a date string to the corresponding file path.
        
        Args:
            date_str: Date in format "YYYY-MM-DD"
            
        Returns:
            Path object to the file
            
        Raises:
            ValueError: If date format is invalid
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            year = date_obj.strftime("%Y")
            month = date_obj.strftime("%m-%b")  # "07-Jul"
            day = date_obj.strftime("%d")
            
            filename = f"max_rarity_binder-{date_str}.txt"
            return self.base_path / year / month / day / filename
        except ValueError as e:
            raise ValueError(f"Invalid date format. Please use YYYY-MM-DD: {e}")
    
    def extract_card_info(self, line: str) -> Tuple[str, str, int]:
        """
        Extract card name, condition, and quantity from the header line.
        
        Args:
            line: Header line containing card info
            
        Returns:
            Tuple of (card_name, condition, quantity)
            
        Raises:
            ValueError: If line cannot be parsed
        """
        # Pattern: "Card Name [rarity] - Condition <quantity>"
        pattern = r'^(.*?)\s+\[.*?\]\s+-\s+(.*?)\s+<(\d+)>$'
        match = re.match(pattern, line.strip())
        
        if match:
            return (
                match.group(1).strip(),
                match.group(2).strip(),
                int(match.group(3))
            )
        raise ValueError(f"Could not parse card info from line: '{line}'")
    
    def extract_price_data(self, data_line: str) -> CardPriceData:
        """
        Extract price data from the data row of the table.
        
        Args:
            data_line: Line containing the price data (| 1999 | 2999 | 2499 | 2499.0 |)
            
        Returns:
            CardPriceData object with parsed values
            
        Raises:
            ValueError: If data cannot be parsed
        """
        clean_line = data_line.strip().strip('|')
        values = [val.strip() for val in clean_line.split('|')]
        
        if len(values) != 4:
            raise ValueError(f"Expected 4 values, got {len(values)}: {values}")
        
        try:
            return CardPriceData(
                min_price=float(values[0]),
                max_price=float(values[1]),
                mean_price=float(values[2]),
                median_price=float(values[3]),
                quantity=0  # Will be set by caller
            )
        except ValueError as e:
            raise ValueError(f"Could not convert values to float: {values}, Error: {e}")
    
    def parse_file(self, file_path: Path) -> List[Tuple[str, CardPriceData, int]]:
        """
        Parse a single file and extract all card data in order.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            List of tuples: (card_key, CardPriceData, quantity) in file order
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        cards_data = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and summary lines
            if not line or line.startswith('Missing Data') or line.startswith('Sum of'):
                i += 1
                continue
            
            # Check if this line is a card header
            if self._is_card_header(line):
                try:
                    card_name, condition, quantity = self.extract_card_info(line)
                    
                    # Look for the data line
                    price_data = self._find_price_data(lines, i)
                    if price_data:
                        price_data.quantity = quantity
                        card_key = f"{card_name} - {condition}"
                        cards_data.append((card_key, price_data, quantity))
                
                except (ValueError, IndexError):
                    pass  # Skip unparseable lines
            
            i += 1
        
        return cards_data
    
    def _is_card_header(self, line: str) -> bool:
        """Check if a line appears to be a card header."""
        return all(marker in line for marker in ['[', ']', '<', '>', '-'])
    
    def _find_price_data(self, lines: List[str], start_index: int) -> Optional[CardPriceData]:
        """
        Find and parse price data starting from the given index.
        
        Args:
            lines: All lines from the file
            start_index: Index to start searching from
            
        Returns:
            CardPriceData if found, None otherwise
        """
        for j in range(start_index + 1, min(start_index + 10, len(lines))):
            data_line = lines[j].strip()
            
            if self._is_data_line(data_line):
                try:
                    return self.extract_price_data(data_line)
                except ValueError:
                    continue
        return None
    
    def _is_data_line(self, line: str) -> bool:
        """Check if a line appears to be a data line."""
        return (line.startswith('|') and 
                line.endswith('|') and
                line.count('|') >= 4 and
                any(char.isdigit() for char in line) and
                not any(word in line for word in ['Min', 'Max', '---']))
    
    def calculate_differences(self, data1: CardPriceData, data2: CardPriceData) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Calculate absolute and percentage differences between two price datasets.
        
        Args:
            data1: First date's price data
            data2: Second date's price data
            
        Returns:
            Tuple of (absolute_diffs, percentage_diffs) dictionaries
        """
        abs_diffs = {
            'min': data2.min_price - data1.min_price,
            'max': data2.max_price - data1.max_price,
            'mean': data2.mean_price - data1.mean_price,
            'median': data2.median_price - data1.median_price
        }
        
        percent_diffs = {}
        for key in ['min', 'max', 'mean', 'median']:
            old_value = getattr(data1, f"{key}_price")
            if old_value != 0:
                percent_diffs[key] = (abs_diffs[key] / old_value) * 100
            else:
                percent_diffs[key] = 0.0
        
        return abs_diffs, percent_diffs
    
    def compare_dates(self, date1: str, date2: str) -> List[CardEntry]:
        """
        Compare card prices between two dates.
        
        Args:
            date1: First date in YYYY-MM-DD format
            date2: Second date in YYYY-MM-DD format
            
        Returns:
            List of CardEntry objects containing comparison data in file order
        """
        file1_path = self.parse_date_to_path(date1)
        file2_path = self.parse_date_to_path(date2)
        
        # Parse both files
        cards1_list = self.parse_file(file1_path)
        cards2_list = self.parse_file(file2_path)
        
        # Convert to dictionaries for lookup
        cards2_dict = {key: (data, qty) for key, data, qty in cards2_list}
        
        # Find common cards while maintaining order from the first file
        comparison_results = []
        
        for card_key, data1, qty1 in cards1_list:
            if card_key in cards2_dict:
                data2, qty2 = cards2_dict[card_key]
                
                # Calculate differences
                abs_diffs, percent_diffs = self.calculate_differences(data1, data2)
                
                # Parse card name and condition
                parts = card_key.rsplit(' - ', 1)
                name = parts[0] if len(parts) == 2 else card_key
                condition = parts[1] if len(parts) == 2 else "Unknown"
                
                # Create CardEntry object
                entry = CardEntry(
                    name=name,
                    condition=condition,
                    date1_data=data1,
                    date2_data=data2,
                    min_diff=abs_diffs['min'],
                    max_diff=abs_diffs['max'],
                    mean_diff=abs_diffs['mean'],
                    median_diff=abs_diffs['median'],
                    min_percent=percent_diffs['min'],
                    max_percent=percent_diffs['max'],
                    mean_percent=percent_diffs['mean'],
                    median_percent=percent_diffs['median'],
                    quantity_diff=qty2 - qty1,
                    date1=date1,
                    date2=date2
                )
                
                comparison_results.append(entry)
        
        return comparison_results
    
    def format_direction_arrow(self, value: float) -> str:
        """
        Return a colored arrow indicating price direction.
        
        Args:
            value: The difference value
            
        Returns:
            String with arrow and color indication
        """
        if value > 0:
            return "✅ ↑"
        elif value < 0:
            return "🔴 ↓"
        else:
            return "⚪ →"
    
    def print_comparison_report(self, results: List[CardEntry]):
        """
        Print a formatted comparison report.
        
        Args:
            results: List of CardEntry objects to display
        """
        if not results:
            print("No comparison data to display")
            return
        
        print(f"\n{'=' * 100}")
        print(f"CARD PRICE COMPARISON REPORT")
        print(f"Date 1: {results[0].date1} | Date 2: {results[0].date2}")
        print(f"{'=' * 100}")
        
        for entry in results:
            print(f"\n{'-' * 80}")
            print(f"Card: {entry.name}")
            print(f"Condition: {entry.condition}")
            print(f"{'-' * 80}")
            
            # Price data table
            print(f"{'Metric':<10} {'Date1':<10} {'Date2':<10} {'Diff':<10} {'%Change':<10} {'Direction':<10}")
            print(f"{'-' * 70}")
            
            metrics = [
                ('Min', entry.date1_data.min_price, entry.date2_data.min_price, entry.min_diff, entry.min_percent),
                ('Max', entry.date1_data.max_price, entry.date2_data.max_price, entry.max_diff, entry.max_percent),
                ('Mean', entry.date1_data.mean_price, entry.date2_data.mean_price, entry.mean_diff, entry.mean_percent),
                ('Median', entry.date1_data.median_price, entry.date2_data.median_price, entry.median_diff, entry.median_percent)
            ]
            
            for metric_name, val1, val2, diff, percent in metrics:
                direction = self.format_direction_arrow(diff)
                print(f"{metric_name:<10} ${val1:<9.0f} ${val2:<9.0f} ${diff:<9.0f} {percent:<9.1f}% {direction}")
            
            print(f"\nQuantity: {entry.date1_data.quantity} → {entry.date2_data.quantity} (Diff: {entry.quantity_diff:+d})")
    
    def export_to_csv(self, results: List[CardEntry], filename: Optional[str] = None) -> str:
        """
        Export comparison results to CSV file.
        
        Args:
            results: List of CardEntry objects to export
            filename: Optional filename, will generate one if not provided
            
        Returns:
            Path to the created CSV file
        """
        # Create output directory
        output_dir = Path("card_price_comparisons")
        output_dir.mkdir(exist_ok=True)

        if not filename:
            if results:
                # Use the dates from the comparison
                date1 = results[0].date1
                date2 = results[0].date2
                filename = f"comparison_{date1}_vs_{date2}.csv"
            else:
                # Fallback if no results
                date_stamp = datetime.now().strftime("%Y-%m-%d")
                filename = f"comparison_{date_stamp}.csv"

        filepath = output_dir / filename

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'card_name', 'condition', 'date1', 'date2',
                'date1_min', 'date1_max', 'date1_mean', 'date1_median', 'date1_quantity',
                'date2_min', 'date2_max', 'date2_mean', 'date2_median', 'date2_quantity',
                'min_diff', 'max_diff', 'mean_diff', 'median_diff',
                'min_percent', 'max_percent', 'mean_percent', 'median_percent',
                'quantity_diff'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for entry in results:
                writer.writerow({
                    'card_name': entry.name,
                    'condition': entry.condition,
                    'date1': entry.date1,
                    'date2': entry.date2,
                    'date1_min': entry.date1_data.min_price,
                    'date1_max': entry.date1_data.max_price,
                    'date1_mean': entry.date1_data.mean_price,
                    'date1_median': entry.date1_data.median_price,
                    'date1_quantity': entry.date1_data.quantity,
                    'date2_min': entry.date2_data.min_price,
                    'date2_max': entry.date2_data.max_price,
                    'date2_mean': entry.date2_data.mean_price,
                    'date2_median': entry.date2_data.median_price,
                    'date2_quantity': entry.date2_data.quantity,
                    'min_diff': entry.min_diff,
                    'max_diff': entry.max_diff,
                    'mean_diff': entry.mean_diff,
                    'median_diff': entry.median_diff,
                    'min_percent': entry.min_percent,
                    'max_percent': entry.max_percent,
                    'mean_percent': entry.mean_percent,
                    'median_percent': entry.median_percent,
                    'quantity_diff': entry.quantity_diff
                })

        print(f"Results exported to: {filepath}")
        return str(filepath)


def main():
    """Main entry point for the card price comparison tool."""
    parser = CardPriceParser()

    # Example usage
    date1 = "2025-01-04"
    date2 = "2025-07-02"

    try:
        results = parser.compare_dates(date1, date2)
        parser.print_comparison_report(results)

        if results:
            parser.export_to_csv(results)
            print(f"\nComparison completed! Found {len(results)} common cards.")
        else:
            print("\nNo common cards found between the two dates.")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
