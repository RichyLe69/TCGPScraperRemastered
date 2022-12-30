# TCGPScraperRemastered

 ![Alpha status](https://img.shields.io/badge/Project%20status-Alpha-red.svg)
 [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
 [![PyPI pyversions](https://camo.githubusercontent.com/fd8c489427511a31795637b3168c0d06532f4483/68747470733a2f2f696d672e736869656c64732e696f2f707970692f707976657273696f6e732f77696b6970656469612d6170692e7376673f7374796c653d666c6174)](https://pypi.python.org/pypi/ansicolortags/)

Update 2023: SellerPortalDatabase no longer works due to some captcha thing, so This will be the new version of YGO Card Scraper.

Data starting from 2023 onwards will be the new data format. 

Superior Version of TCGPlayer Scraper. This version uses the Portal Seller database instead of the public listings. This is significantly more accurate as now I have access to last sold prices. In addition, I'm taking into account pricing difference of foreign cards. 

Automated WebScraper using Selenium Webdriver and data parsers to automatically retrieve any amount and any specified card based on the configs.

The WebDriver handles all the operations and saves the data in plain text tables for ease of analysis.

This program is incredibly useful for auditing any sort of card collection as long as the TCGPlayer database and live listings are accurate.

The configurations can be found in the .yaml files which contain all the data needed for the data collection process.

Simply use the following config structure and add in as many items as needed:

```
Card Name:
  url: '' # ID Number of Portal Seller Card Database 
  edition: 'Near Mint' # card condition
  qty: 1 # Number of cards 
```

# A Typical output for a single entry:

```
Stardust Dragon Ghost 1st [1] - Near Mint 1st
+------------+---------------+------------------+
| TCG Lowest | TCG Last Sold | TCG Market Price |
+------------+---------------+------------------+
|    2499    |      1999     |       1612       |
+------------+---------------+------------------+
```

Card name and quantity on top with condition and edition.
Table Data shows:
```
TCG Lowest: Lowest current live listing
TCG Last Sold: Price of the most recent sold card of respective 
TCG Market Price: Based on average calculation of previous few sold
```
Intended to keep track of my personal e-commerce inventory.
