import requests
from bs4 import BeautifulSoup
import re
import csv
from urllib.parse import urljoin, urlparse
import phonenumbers
import datetime
import time
import random


def find_emails(text):
    return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}", text)


def find_phone_numbers(text, default_region="US"):
    parsed_numbers = []
    for match in phonenumbers.PhoneNumberMatcher(text, default_region):
        parsed_numbers.append(
            phonenumbers.format_number(
                match.number, phonenumbers.PhoneNumberFormat.E164
            )
        )
    return parsed_numbers


def find_names(text):
    # Modify this regex pattern to match your required name format
    return re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)


def save_to_csv(data, file_name_prefix="scraped_data"):
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    file_name = f"{file_name_prefix}_{current_date}.csv"
    with open(file_name, "w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["URL", "Emails"])
        for row in data:
            csv_writer.writerow(row)


def find_links(soup, base_url):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("#"):
            url = urljoin(base_url, href)
            parsed_url = urlparse(url)
            if parsed_url.scheme in ["http", "https"]:
                links.add(url)
    return links


def find_links_v2(soup, base_url):
    links = set()
    base_netloc = urlparse(base_url).netloc

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("#"):
            url = urljoin(base_url, href)
            parsed_url = urlparse(url)
            if (
                parsed_url.scheme in ["http", "https"]
                and parsed_url.netloc == base_netloc
            ):
                links.add(url)
    return links


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

DELAY = 5  # Adjust the delay in seconds as needed

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15",
    # Add more user agents as needed
]


def random_user_agent():
    return {"User-Agent": random.choice(USER_AGENTS)}


def scrape_website(url, visited_urls, depth=0, max_depth=2):
    if depth > max_depth or url in visited_urls:
        return [], []

    visited_urls.add(url)
    print(f"running scrape_website on {url} (depth: {depth})")

    try:
        response = requests.get(url, headers=random_user_agent())
        time.sleep(DELAY)

    except requests.exceptions.RequestException as e:
        print(f"Error while requesting {url}: {e}")
        return [], []
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text()
    # print("text: ", text)

    emails = find_emails(text)
    phone_numbers = find_phone_numbers(text)
    # names = find_names(text)
    if depth < max_depth:
        links = find_links_v2(soup, url)
        for link in links:
            sub_emails, sub_phone_numbers = scrape_website(
                link, visited_urls, depth + 1, max_depth
            )
            emails.extend(sub_emails)
            phone_numbers.extend(sub_phone_numbers)
            # names.extend(sub_names)

    return (
        emails,
        phone_numbers,
    )  # names


def scrape_websites_deep_search(urls, max_depth=2):
    scraped_data = []
    for url in urls:
        visited_urls = set()
        emails, phone_numbers = scrape_website(url, visited_urls, 0, max_depth)
        scraped_data.append(
            [
                url,
                ", ".join(emails),
                ", ".join(phone_numbers),
            ]
        )
    save_to_csv(scraped_data, "scraped_data")
    return scraped_data
