import urllib.request
from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.parse import urljoin, urlparse

# Connect to MongoDB
def connect_to_database():
    DB_NAME = "CPP"
    DB_HOST = "localhost"
    DB_PORT = 27017

    try:
        client = MongoClient(host=DB_HOST, port=DB_PORT)
        db = client[DB_NAME]
        return db
    except Exception as e:
        print("Database connection error:", e)
        return None

# Function to retrieve HTML content from a URL
def retrieve_html(url):
    try:
        with urllib.request.urlopen(url) as response:
            html_content = response.read().decode("utf-8")
            return html_content
    except Exception as e:
        print("Error retrieving HTML for URL:", url)
        return None

# Function to store page data in MongoDB
def store_page(url, html_content, collection):
    if html_content:
        try:
            collection.insert_one({"url": url, "html_content": html_content})
            print("Page stored in MongoDB:", url)
        except Exception as e:
            print("Error storing page in MongoDB:", e)

# Function to check if target page is found
def target_page(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for heading in headings:
        if heading.text.strip() == "Permanent Faculty":
            return True
    return False

# Function to parse pages and extract links
def parse_links(html_content, base_url):
    links = []
    soup = BeautifulSoup(html_content, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if href:
            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)
            # Consider only HTML or SHTML pages
            if parsed_url.path.endswith(('.html', '.shtml')):
                links.append(absolute_url)
    return links

# Main crawler function following pseudocode
def crawler_thread(frontier, target_url, collection):
    while not frontier.done():
        url = frontier.next_url()
        html_content = retrieve_html(url)
        store_page(url, html_content, collection)
        if target_page(html_content):
            print("Target page found:", url)
            break
        else:
            links = parse_links(html_content, url)
            for link in links:
                frontier.add_url(link)

# Class for Frontier
class Frontier:
    def __init__(self, base_url):
        self.visited_urls = set()
        self.url_queue = [base_url]

    def add_url(self, url):
        if url not in self.visited_urls and url not in self.url_queue:
            self.url_queue.append(url)

    def next_url(self):
        if self.url_queue:
            next_url = self.url_queue.pop(0)
            self.visited_urls.add(next_url)
            return next_url
        else:
            return None

    def done(self):
        return len(self.url_queue) == 0

def main():
    base_url = "https://www.cpp.edu/sci/computer-science/"
    target_url = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"
    # Initializing the frontier
    frontier = Frontier(base_url)

    db = connect_to_database()
    if db is None:
        print("Failed to connect to the database.")
        return

    # Crawl the frontier until target page is found
    crawler_thread(frontier, target_url, db["pages"])


if __name__ == "__main__":
   main()
