import os
import csv
import sqlite3
import requests
import chardet
from bs4 import BeautifulSoup
from tqdm import tqdm

# Define input and output file paths
url_list_file = '../../data/site-profiles/domainlist2.csv'
# db_file = '../data/sites3.db'
db_file = '../../data/site-profiles/sites-profiles.db'

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Brave";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'sec-ch-ua-platform': '"macOS"',
}
timeout = 7
fetch_errors = 0
is_wp_count = 0
rss_count = 0
# Create SQLite database and table if it doesn't exist
conn = sqlite3.connect(db_file)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                url TEXT,
                title TEXT,
                description TEXT,
                rss TEXT,
                is_wp INTEGER,
                wp_json INTEGER,
                sitemap TEXT,
                response_time REAL,
                page_size_html REAL,
                page_size_text REAL,
                ssl INTEGER,
                etag TEXT,
                fetch_date TEXT,
                ip TEXT
                )''')
conn.commit()

# Function to fetch a URL and handle redirects
def fetch_url(url):
    try:
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)

        response.raise_for_status()

        # Check if the URL was redirected and update the final URL
        final_url = response.url

        # Fetch page encoding
        encoding = chardet.detect(response.content)['encoding']

        # Explicitly specify the encoding when decoding the content
        page_content = response.content.decode(encoding)

        # Update counters
        global is_wp_count, rss_count
        is_wp_count += 1 if "/wp-content/" in page_content or "/wp-includes/" in page_content else 0
        # You can implement RSS detection logic and update rss_count here

        return final_url, page_content, encoding

    except requests.exceptions.RequestException as e:
        # Update fetch error count
        global fetch_error_count
        fetch_error_count += 1
        return None, str(e), None

# Function to extract page title
def extract_title(html):
    soup = BeautifulSoup(html, 'html.parser')
    title_tag = soup.find('title')
    return title_tag.text if title_tag else None

# Function to extract page description
def extract_description(html):
    soup = BeautifulSoup(html, 'html.parser')
    meta_description = soup.find('meta', attrs={'name': 'description'})
    og_description = soup.find('meta', attrs={'property': 'og:description'})
    description = []

    if meta_description:
        description.append(meta_description['content'])
    
    if og_description:
        description.append(og_description['content'])

    return ' || '.join(description) if description else None

# Function to check if a URL exists
def url_exists(url):
    try:
        response = requests.head(url, headers={"User-Agent": "Mozilla/5.0"})
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Read domains from the CSV file and process them
with open(url_list_file, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # Skip the header row

    for row in tqdm(csvreader, desc="Processing URLs"):
        domain = row[0]
        tqdm.write(domain)
        url = f"https://{domain}"
        if not url_exists(url) and not domain.startswith('www.'):
            url = f"https://www.{domain}"

        final_url, page_content, encoding = fetch_url(url)

        if final_url:
            title = extract_title(page_content)
            description = extract_description(page_content)
            is_wp = 1 if "/wp-content/" in page_content or "/wp-includes/" in page_content else 0
            wp_json_url = f"{final_url}/wp-json/"
            wp_json_exists = 1 if url_exists(wp_json_url) else 0
            sitemap_url = f"{final_url}sitemap.xml"
            sitemap_exists = 1 if url_exists(sitemap_url) else 0
            response_time = requests.get(final_url).elapsed.total_seconds()
            page_size_html = len(page_content) / (1024 * 1024)
            page_size_text = len(' '.join(BeautifulSoup(page_content, 'html.parser').stripped_strings)) / (1024 * 1024)
            ssl = 1 if final_url.startswith("https://") else 0
            etag = None  # You can implement this if needed
            fetch_date = None  # You can implement this if needed
            ip = None  # You can implement this if needed
        else:
            title = "Fetch Error"
            description = "Fetch Error"
            is_wp = 0
            wp_json_exists = 0
            sitemap_exists = 0
            response_time = None
            page_size_html = -1
            page_size_text = -1
            ssl = 0
            etag = None
            fetch_date = None
            ip = None
            fetch_errors += 1

        if is_wp:
            is_wp_count += 1

        # Process RSS feeds if found
        # Modify this part according to how you detect RSS feeds
        rss_feeds = []
        if "rss" in page_content.lower():
            rss_feeds.append("RSS Feed 1")
            rss_feeds.append("RSS Feed 2")
            # Add more feeds as needed

        if rss_feeds:
            rss_count += 1

        cursor.execute('''INSERT INTO sites (domain, url, title, description, is_wp, wp_json, sitemap, 
                        response_time, page_size_html, page_size_text, ssl, etag, fetch_date, ip) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (domain, final_url, title, description, is_wp, wp_json_exists, sitemap_exists,
                        response_time, page_size_html, page_size_text, ssl, etag, fetch_date, ip))
        conn.commit()

conn.close()
print(f"Data processing completed and saved to the database.")
print(f"Fetch Errors: {fetch_errors}")
print(f"Is WP: {is_wp_count}")
print(f"RSS Feeds Found: {rss_count}")
