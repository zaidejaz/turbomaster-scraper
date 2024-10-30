import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to fetch and parse HTML content
def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.content, 'html.parser')

# Function to find subseries links
def find_subseries_links(soup):
    subseries_links = []
    elements = soup.find_all('div', class_='elementor-column elementor-col-10 elementor-md-15 elementor-sm-33 csubseries')
    for elem in elements:
        link_tag = elem.find('a')
        if link_tag:
            subseries_links.append(link_tag['href'])
    logging.info(f'Found {len(subseries_links)} subseries links.')
    return subseries_links

# Function to scrape table data
def scrape_table(soup):
    table = soup.find('table', {'id': 'table_id'})
    if not table:
        logging.warning('Table not found on the page.')
        return None

    # Get table headers
    headers = [header.text for header in table.find_all('th')]

    # Get table rows
    rows = []
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if cells:
            rows.append([cell.text.strip() for cell in cells])

    return pd.DataFrame(rows, columns=headers)

# Function to handle pagination and scrape all table data
def scrape_paginated_table(url):
    all_data = []
    page = 1

    while True:
        soup = get_soup(url)
        data = scrape_table(soup)
        if data is not None:
            all_data.append(data)

        next_button = soup.find('a', {'class': 'paginate_button next', 'id': 'table_id_next'})
        if not next_button or 'disabled' in next_button.get('class', []):
            break

        page += 1
        url = next_button['href']  # Update URL for the next page

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        logging.warning(f'No data found at {url}')
        return pd.DataFrame()  # Return an empty DataFrame

# Function to extract brand name from URL
def extract_brand_name(url):
    match = re.search(r'/catalogs/([^/]+)/', url)
    return match.group(1).capitalize() if match else 'Unknown'

# Main function to run the scraper
def main(urls):
    all_data = []

    for url in urls:
        logging.info(f'Processing URL: {url}')
        brand_name = extract_brand_name(url)
        soup = get_soup(url)
        subseries_links = find_subseries_links(soup)

        for sub_link in subseries_links:
            full_link = f'https://www.turbomaster.com{sub_link}'
            logging.info(f'Scraping data from subseries link: {full_link}')
            data = scrape_paginated_table(full_link)
            if not data.empty:
                # Insert a row with the brand name before each data
                brand_row = pd.DataFrame([[brand_name] + [''] * (len(data.columns) - 1)], columns=data.columns)
                all_data.append(brand_row)
                all_data.append(data)

    if all_data:
        # Combine all data into a single DataFrame
        final_data = pd.concat(all_data, ignore_index=True)
        # Save the data to an Excel file
        final_data.to_excel('scraped_data.xlsx', index=False)
        logging.info('Data saved to scraped_data.xlsx')
    else:
        logging.warning('No data was scraped from any URL.')

# List of URLs to process
urls = [
    'https://www.turbomaster.com/eng/catalogs/toyota/',
    'https://www.turbomaster.com/eng/catalogs/bosch-mahle/',
    'https://www.turbomaster.com/eng/catalogs/cz/',
    'https://www.turbomaster.com/eng/catalogs/continental/',
    'https://www.turbomaster.com/eng/catalogs/komatsu/',
    'https://www.turbomaster.com/eng/catalogs/holset/', 
    'https://www.turbomaster.com/eng/catalogs/borgwarner/',
    'https://www.turbomaster.com/eng/catalogs/ihi/',
    'https://www.turbomaster.com/eng/catalogs/garrett/',
    'https://www.turbomaster.com/eng/catalogs/mitsubishi/',
    'https://www.turbomaster.com/eng/catalogs/hitachi/',
]

# Run the scraper
if __name__ == '__main__':
    main(urls)
