# TRESPASSERS OSINT by r4nsom

## Overview

`TRESPASSER` is a Python script that performs web scraping to extract various data from a given website. It collects emails, phone numbers, usernames, addresses, and full names. The results are then presented and can be saved to a .txt or .json file.

## Features

- **Web Scraping**: Extracts emails, phone numbers, usernames, addresses, and full names.
- **Phone Number Patterns**: Supports phone number formats for multiple countries.
- **Common Names**: Filters full names against a list of common names trough API.
- **Results Summary**: Displays a summary of the extracted data.
- **Save Results**: Option to save results to a text or JSON file.
- **User Interface**: Simple file dialog for saving results.

## Requirements

- Python 3.x
- `requests`
- `pyfiglet`
- `tkinter` (typically included with Python)
- `scrapy`
- `keyboard`

You can install the required packages using pip:

pip install -r requirements.txt

## To run

sudo python3 trespasser.py
