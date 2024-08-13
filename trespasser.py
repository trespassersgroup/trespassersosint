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
import logging
import keyboard  # Import the keyboard module
from colorama import init, Fore, Style

# Initialize colorama
init()

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
        logging.getLogger('scrapy').setLevel(logging.ERROR)  # Suppress unwanted log messages
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

def search_email(email):
    url = "https://leakpeek.com/inc/iap16"
    
    params = {
        "id": "89473",
        "query": email,
        "t": "1723526678",  # Make sure this timestamp is updated or dynamically generated if needed
        "input": email
    }
    
    headers = {
        "Host": "leakpeek.com",
        "Cookie": "PHPSESSID=c02iaeniu6sssf3c8agsb2pq2v; twk_idm_key=pELXrZWyM2clCRsh0XQCu; TawkConnectionTime=0; twk_uuid_5e0a72c07e39ea1242a266c8=%7B%22uuid%22%3A%221.Swu9WRgNiTkF96aDPACGDtR6Kn8OLaZRTVvC8pumfepgYp554l3ejNXpuOaGa6Xwtoevfd1H5foznyDxCBJUedoUXV4GHNzwqp9XyAcgyf0h5UBkNSe2h%22%2C%22version%22%3A3%2C%22domain%22%3A%22leakpeek.com%22%2C%22ts%22%3A1723526654188%7D",
        "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\"",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Sec-Ch-Ua-Platform": "\"Linux\"",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://leakpeek.com/?",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        print(Fore.YELLOW + "\nSearching for information..." + Style.RESET_ALL)
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        
        # Extracting email information
        emails = data.get("emails", [])
        results = []

        if not emails:
            print(Fore.RED + "No data found for this email." + Style.RESET_ALL)
            return results

        for entry in emails:
            email = entry.get("email")
            password = entry.get("password")
            sources = entry.get("sources", [])
            
            results.append({
                "email": email,
                "password": password,
                "sources": sources
            })

        return results
    
    except requests.RequestException as e:
        print(Fore.RED + f"An error occurred: {e}" + Style.RESET_ALL)
        return []

def print_divider(color):
    print(color + "-"*50 + RESET)

def main():
    print_figlet_greeting()
    time.sleep(5)
    os.system('cls' if platform.system() == 'Windows' else 'clear')

    prompt = f"{BLUE}Enter URL or email address: {RESET}"
    user_input = input(prompt).strip()

    if re.match(r'^[\w.-]+\.[a-zA-Z]{2,}$', user_input):
        full_url = f"http://{user_input}"
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
        process.crawl(DataSpider, start_url=user_input)
        process.start()

    elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', user_input):
        print(f"{YELLOW}Searching for information on email...{RESET}")
        results = search_email(user_input)
        
        if results:
            print_divider(YELLOW)
            print(Fore.LIGHTYELLOW_EX + "\nExtracted Information:" + Style.RESET_ALL)
            for result in results:
                print(Fore.BLUE + "Email:" + Style.RESET_ALL + Fore.WHITE + f" {result['email']}" + Style.RESET_ALL)
                print(Fore.BLUE + "Password:" + Style.RESET_ALL + Fore.WHITE + f" {result['password']}" + Style.RESET_ALL)
                print(Fore.BLUE + "Sources:" + Style.RESET_ALL + Fore.WHITE + f" {', '.join(result['sources'])}" + Style.RESET_ALL)
                print_divider(YELLOW)
            
            print(f"{BLUE}Press {GREEN}Y{RESET} {BLUE}to save results or {RED}X{BLUE} to exit.{RESET}")
            while True:
                if keyboard.is_pressed('y'):
                    print(f"{GREEN}Saving results...{RESET}")
                    save_results_to_file(results)
                    break
                elif keyboard.is_pressed('x'):
                    print(f"{RED}Results not saved.{RESET}")
                    break
        else:
            print(f"{RED}No information found or an error occurred.{RESET}")

    else:
        print(f"{RED}Invalid input. Please enter a valid URL or email address.{RESET}")

def save_results_to_file(results):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                           filetypes=[("Text files", "*.txt"), ("JSON file", "*.json"), ("All files", "*.*")])
    if file_path:
        try:
            with open(file_path, 'w') as file:
                for result in results:
                    file.write(f"Email: {result['email']}\n")
                    file.write(f"Password: {result['password']}\n")
                    file.write(f"Sources: {', '.join(result['sources'])}\n")
                    file.write("\n" + "-"*50 + "\n")
            print(Fore.GREEN + f"Results saved to {file_path}." + Style.RESET_ALL)
        except IOError as e:
            print(Fore.RED + f"Failed to save results: {e}" + Style.RESET_ALL)
    else:
        print(Fore.RED + "Save operation was cancelled." + Style.RESET_ALL)

if __name__ == "__main__":
    main()
