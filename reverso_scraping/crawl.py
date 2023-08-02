import csv
import os

import requests
import urllib.parse
from bs4 import BeautifulSoup

def crawl_top(targetURL, onlyNames=False, ranking=False):
    """ Crawls top list or ranking page looking for links to target words/expressions """

    # Reverso requires user-agent, otherwise it will refuse the request
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
    }

    req = requests.get(targetURL, headers=headers)
    if req.status_code == 200:
        path = urllib.parse.urlparse(targetURL).path
        name = os.path.splitext(os.path.basename(path))[0]

        os.makedirs('crawled/txt/', exist_ok=True)
        with open(f"crawled/txt/crawl_{name}.txt", "w+", encoding="utf-8") as crawl:
            print("Successful GET request!")

            # Extract the HTML content from the URL for parsing
            content = req.content
            html = BeautifulSoup(content, "html.parser")

            topListDiv = html.find("div", class_="top_list")
            links = topListDiv.find_all("a")

            # Ex: /index/frances-portugues/w.html
            if ranking:
                hrefs = [link["href"] for link in links]
            else:  # Ex: /index/frances-portugues/w-1-300.html
                # top lists have 'In Simon we trust' unwanted URL (easter egg?)
                hrefs = [link["href"] for link in links[:-1]]


            if onlyNames:
                extracted_names = [link.text for link in links]
                for name in extracted_names:
                    crawl.write(f"{name}\n")
                return extracted_names
            else:
                for href in hrefs:
                    crawl.write(f"{href}\n")
                return hrefs


def crawl_all(type = 'p'):
    base_url = f"https://context.reverso.net/traducao/index/frances-portugues/{type}.html"

    # First, get the URLs for the ranking pages
    ranking_urls = crawl_top(base_url, ranking=True)

    # Then, iterate over the ranking pages and get the names on each page
    os.makedirs('crawled/csv', exist_ok=True)
    for ranking_url in ranking_urls:
        names = crawl_top(ranking_url, onlyNames=True, ranking=False)

        # Extract subranking identifier from the URL
        subranking = ranking_url.split('/')[-1].split('.')[0]  # e.g. p-401-800
        # Create a CSV file for this subranking
        with open(f'crawled/csv/{subranking}.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Name', 'URL'])  # CSV header

            for name in names:
                # Build Reverso URL for each name
                name_url = f"https://context.reverso.net/traducao/frances-portugues/{urllib.parse.quote(name)}"
                writer.writerow([name, name_url])
            print(f"Finished crawling {subranking}")
