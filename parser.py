#-------------------------------------------------------------------------
# AUTHOR: James Avila
# FILENAME: parser.py
# SPECIFICATION: This file parsers the html content of the target url,
# specifically: professor name, title, officem phone number, email,
# and website. This information is then stored in a mongodb collection
# called "professors"
# FOR: CS 4250- Assignment #4
# TIME SPENT: 1.5 hours
#-----------------------------------------------------------*/

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

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

# Target URL
url = 'https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml'

# Remove unnecessary colons in fields except email
def remove_colons(professor):
    for key, value in professor.items():
        if key != 'email':
            professor[key] = value.replace(': ', '')
    return professor

def parse_faculty(html_content, collection):
    soup = BeautifulSoup(html_content, 'html.parser')
    professor_containers = soup.find_all('div', class_='clearfix')
    for container in professor_containers:
        professor = {}
        # Extracting information for each professor
        name_element = container.find('h2')
        if name_element:
            name = name_element.text.strip()
            professor['name'] = name
        else:
            print("Name not found for professor.")
            continue

        info_items = container.find_all('strong')
        for item in info_items:
            label_text = item.text.strip()
            # Remove colon if it exists in label
            label = label_text.replace(':', '').lower()
            # Get next sibling text or empty string
            value = item.next_sibling.strip() if item.next_sibling else ""
            # If value is empty, try to get text from the next sibling
            if not value and item.next_sibling:
                value = item.next_sibling.next_sibling.text.strip() if item.next_sibling.next_sibling else ""
            # Add label and value to professor dictionary
            professor[label] = value

        # Additional processing for email and website
        email = container.find('a', href=lambda href: href and 'mailto' in href)
        if email:
            professor['email'] = email.text.strip()

        website = container.find('a', href=lambda href: href and 'mailto' not in href)
        if website:
            professor['web'] = website['href']

        professor = remove_colons(professor)

        # Inserting professor data into MongoDB
        try:
            collection.insert_one(professor)
            print("Saved professor:", professor['name'])
        except Exception as e:
            print("Error saving professor:", e)



def main():
    # Connect to MongoDB
    db = connect_to_database()
    if db is None:
        return

    # Initialize MongoDB collection
    collection = db['professors']

    # Fetch HTML content
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.content
        # Parse and store faculty information
        parse_faculty(html_content, collection)
        print("Faculty information successfully parsed and stored in MongoDB.")
    else:
        print("Failed to fetch HTML content from the target URL.")

if __name__ == "__main__":
    main()
# type: ignore