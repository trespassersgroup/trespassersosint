import os
import platform
import sys
import time
import re
import requests
import pyfiglet
import tkinter as tk
from tkinter import filedialog
from requests.exceptions import RequestException
from urllib.parse import urljoin, urlparse
import scrapy
from scrapy.crawler import CrawlerProcess
import keyboard

# Terminal color codes
GREEN = '\033[92m'
RED = '\033[91m'
WHITE = '\033[97m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Figlet greeting
def print_figlet_greeting():
    os.system('cls' if platform.system() == 'Windows' else 'clear')
    print(f"{BLUE}{pyfiglet.figlet_format('TRESPASSERS', font='slant')}{RESET}")
    print(f"{YELLOW}Script is loading up...{RESET}")
    print(f"{YELLOW}CONTACT:{RESET} {RED}trespassersgroup@proton.me{RESET}\n")

class DataSpider(scrapy.Spider):
    name = 'data_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_url = kwargs.get('start_url')
        self.base_domain = urlparse(f"http://{self.start_url}").netloc
        self.emails = set()
        self.phones = set()
        self.usernames = set()
        self.addresses = set()
        self.full_names = set()
        self.visited_urls = set()
        self.country_code = kwargs.get('country_code', '1')
        self.phone_patterns = self._initialize_phone_patterns()
        self.current_pattern = self.phone_patterns.get(self.country_code, r'\+\d[\d -]{8,15}')
        self.username_pattern = re.compile(r'@[\w_]+')
        self.address_pattern = re.compile(r'\d{1,5}\s\w+(\s\w+)+,?\s\w+(\s\w+)*,\s\w{2,3}\s\d{5}')
        self.full_name_pattern = re.compile(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b')
        self.fetch_common_names()

    def fetch_common_names(self):
        try:
            response = requests.get('https://randomuser.me/api/?results=1000')
            response.raise_for_status()
            self.common_names = {f"{user['name']['first']} {user['name']['last']}".lower()
                                 for user in response.json()['results']}
        except RequestException as e:
            print(f"{RED}Error fetching names from API: {e}{RESET}")
            self.common_names = set()

    def _initialize_phone_patterns(self):
        return {
            '1': r'\+1\d{10}', '44': r'\+44\d{10}', '61': r'\+61\d{9}', '49': r'\+49\d{11}',
            '33': r'\+33\d{9}', '39': r'\+39\d{10}', '34': r'\+34\d{9}', '55': r'\+55\d{11}',
            '86': r'\+86\d{11}', '91': r'\+91\d{10}', '27': r'\+27\d{10}', '82': r'\+82\d{10}',
            '81': r'\+81\d{10}', '7': r'\+7\d{10,11}', '31': r'\+31\d{9}', '46': r'\+46\d{10}',
        }

    def start_requests(self):
        url = f"http://{self.start_url}"
        self.visited_urls.add(url)
        yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        text = response.text
        self.emails.update(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
        self.phones.update(self.clean_phone_number(phone) for phone in re.findall(r'\+\d[\d -]{8,15}', text)
                           if self.is_valid_phone_number(self.clean_phone_number(phone)))
        self.usernames.update(self.username_pattern.findall(text))
        self.addresses.update(self.address_pattern.findall(text))
        self.full_names.update(name for name in self.full_name_pattern.findall(text)
                               if name.lower() in self.common_names)
        self._follow_links(response)

    def _follow_links(self, response):
        for href in response.css('a::attr(href)').getall():
            url = urljoin(response.url, href)
            if urlparse(url).netloc == self.base_domain and url not in self.visited_urls:
                self.visited_urls.add(url)
                yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def clean_phone_number(self, phone):
        return re.sub(r'[^\d+]', '', phone)

    def is_valid_phone_number(self, phone):
        return re.match(self.current_pattern, phone) is not None

    def closed(self, reason):
        self._print_summary()
        self._ask_to_save_results()

    def _print_summary(self):
        for item_type, items in [('email', self.emails), ('phone number', self.phones),
                                 ('username', self.usernames), ('address', self.addresses),
                                 ('full name', self.full_names)]:
            count = len(items)
            print(f"\n{GREEN}[+] {RESET}Found {count} {item_type}(s):")
            if count:
                print(f"{YELLOW}{'='*40}{RESET}")
                print('\n'.join(sorted(items)))
                print(f"{YELLOW}{'='*40}{RESET}")
            else:
                print(f"{RED}[-] {WHITE}No {item_type}s found.{RESET}")

    def _ask_to_save_results(self):
        if any([self.emails, self.phones, self.usernames, self.addresses, self.full_names]):
            print(f"\n{BLUE}Press {GREEN}Y{RESET} {BLUE}to save results or {RED}X{BLUE} to exit.{RESET}")
            while True:
                if keyboard.is_pressed('y'):
                    print(f"{GREEN}Saving results...{RESET}")
                    self._save_results_to_file()
                    break
                elif keyboard.is_pressed('x'):
                    print(f"{RED}Results not saved.{RESET}")
                    break

    def _save_results_to_file(self):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt"), ("JSON file", "*.json"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as f:
                for label, items in [('Emails', self.emails), ('Phone Numbers', self.phones),
                                     ('Usernames', self.usernames), ('Addresses', self.addresses),
                                     ('Full Names', self.full_names)]:
                    if items:
                        f.write(f'{label}:\n')
                        f.write('\n'.join(sorted(items)) + '\n\n')
            print(f"{GREEN}Results saved to {file_path}{RESET}")
        else:
            print(f"{RED}Save operation cancelled.{RESET}")

def check_url_connectivity(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except RequestException:
        return False

def main():
    print_figlet_greeting()
    time.sleep(5)
    os.system('cls' if platform.system() == 'Windows' else 'clear')

    # Print the prompt in blue
    prompt = f"{BLUE}Enter URL (e.g. example.com): {RESET}"
    start_url = input(prompt).strip()

    if not re.match(r'^[\w.-]+\.[a-zA-Z]{2,}$', start_url):
        print(f"{RED}Invalid URL format!{RESET}")
        sys.exit(1)

    full_url = f"http://{start_url}"

    if not check_url_connectivity(full_url):
        print(f"{RED}Unable to connect to URL!{RESET}")
        sys.exit(1)

    process = CrawlerProcess(settings={
        'FEEDS': {
            'output.json': {
                'format': 'json',
                'overwrite': True
            }
        },
        'LOG_LEVEL': 'ERROR',  # Suppresses INFO and DEBUG logs
    })
    process.crawl(DataSpider, start_url=start_url)
    process.start()

if __name__ == "__main__":
    main()
