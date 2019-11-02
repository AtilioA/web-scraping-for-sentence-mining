import re
import sys
import requests
from bs4 import BeautifulSoup
import shutil
import itertools


def download_file(url):
    """ Downloads url to audios folder """

    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        with open(f"audios/{local_filename}", 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename


def format_french_sentence(sentence):
    """ Cleans a french sentence. Returns the new sentence """

    # Removes div tags
    sentence = sentence.replace("""<div class="post__player-title">""", '')
    sentence = sentence.replace("</div>", '').strip()

    # Replaces <strong> tags with bold and underline
    sentence = re.sub(r"<strong>\s*", "<u><b>", sentence)
    sentence = re.sub(r"(\W*)\s*<\/strong>", r"</u></b>\1", sentence)
    sentence = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", sentence)

    # Removes extra whitespace
    sentence = sentence.replace("  ", " ")

    # Adds full stop if necessary
    # print(sentence)
    sentence = re.sub(r"(\w+)\Z", r"\1.\'", sentence)
    sentence = re.sub(r"(<\/u><\/b>)\Z", r"\1.", sentence)

    return sentence


def format_portuguese_sentence(sentence):
    """ Cleans a portuguese sentence. Returns the new sentence """

    # Removes div tags and extra whitespace
    sentence = re.sub(r"\s\s+", ' ', sentence)
    sentence = sentence.replace("""<div class="post__player-sentence">""", '')
    sentence = sentence.replace("</div>", '').strip()
    # print(sentence)

    # Replaces <strong> tags with bold and underline
    sentence = re.sub(r"<strong>\s*", "<u><b>", sentence)
    sentence = re.sub(r"(\W*)\s*<\/strong>", r"</u></b>\1", sentence)
    sentence = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", sentence)

    # Adds full stop if necessary
    sentence = re.sub(r"(\w+)\Z", r"\1.", sentence)
    sentence = re.sub(r"(<\/u><\/b>)\Z", r"\1.", sentence)
    # print(sentence)

    return sentence


def post_to_card(targetPost):
    """ Scrap a page for its french sentence,
    portuguese sentence and download the corresponding audios.
    Write these infos into a .csv file for Anki importing
    """

    name = targetPost.split('/')[3]
    with open(f"csv/{name}.csv", "w+", encoding="utf8") as card:
        frenchSentences = list()
        portugueseSentences = list()
        audiosFilenames = list()

        req = requests.get(targetPost)
        if req.status_code == 200:
            print('Successful GET request!')

            # Retrieving the html content
            content = req.content
            html = BeautifulSoup(content, 'html.parser')

            # Extracting french sentences
            for div in html.select('div'):
                try:
                    if "post__player-title" in div["class"]:
                        frenchSentences.append(format_french_sentence(str(div)))
                except KeyError:
                    pass
            # print(frenchSentences)

            # Extracting portuguese sentences
            for div in html.select('div'):
                try:
                    if "post__player-text" in div["class"]:
                        portugueseSentences.append(format_portuguese_sentence(str(div)))
                except KeyError:
                    pass
            # print(portugueseSentences)

            # Extracting audios URLs and downloading audios
            for p in html.select('audio'):
                localFilename = download_file(p.source["src"])
                audiosFilenames.append(localFilename)
                print(f"Downloading {localFilename}...")
            # print(audiosFilenames)

            if len(frenchSentences) != len(portugueseSentences) != len(audiosFilenames):
                print("Lists don't have all the same length. Output may be compromised.\n")
            # Writing to .csv according to card's fields
            cardInfos = [x for x in itertools.chain.from_iterable(itertools.zip_longest(frenchSentences, portugueseSentences, audiosFilenames)) if x]
            for i in range(0, len(cardInfos) - 2, 3):
                card.write(f"{cardInfos[i]}|{cardInfos[i + 1]}|[sound:{cardInfos[i + 2]}]|frances_fluente\n")
        else:
            print("Failed GET request.")


def crawl_page(targetPage):
    """ Crawls the target page ("Francês Fluente") to get
    posts URLs. Save URLs whose posts have been labeled with specific categories
    """

    page = 1  # Starting page
    crawledLinks = list()  # Storing crawled links
    crawlerLimit = 0  # Limit for crawling
    with requests.Session() as session:
        while True:
            found = 0
            response = session.post("https://www.francesfluente.com/wp-admin/admin-ajax.php", data={'action': 'loadmore', 'query': 'null', 'page': page})

            if response.status_code == 200:
                print('Successful POST request!')
                # Retrieving the HTML content
                content = response.content

                # Extracting audios URLs
                html = BeautifulSoup(content, 'html.parser')

                results = html.select('a')
                for post in results:
                    if "Como se diz" in str(post)\
                        or "Expressões" in str(post)\
                        or "significa" in str(post)\
                        or "gírias" in str(post):
                        found = 1
                        print(post['href'])
                        crawledLinks.append(post['href'])
            else:
                print("Failed POST request.")
                break

            # Workaround for when the crawler can't find more posts
            if (found == 0):
                crawlerLimit += 1
            if crawlerLimit >= 2:
                print("Not finding any more posts. Ending crawler.")
                break

            page += 1

        # Saves posts URLs to a .txt file
        with open("posts_urls.txt", "w+", encoding="UTF8") as URLsFile:
            for post in crawledLinks:
                URLsFile.write(f"{post}\n")
    pass


def scrap_pages(postsURLsFile):
    """ Scrap the URLs stored in the .txt file """

    with open(postsURLsFile) as f:
        urls = f.readlines()
    print(f"{len(urls)} URLs found.")
    urlCounter = 1
    for url in urls:
        print(f"Scraping post number {urlCounter}: {url}...")
        post_to_card(url)
        urlCounter += 1


if __name__ == "__main__":
    try:
        if sys.argv[1].lower() == 'c':
            crawl_page("https://francesfluente.com")
    except IndexError:
        crawl_page("https://francesfluente.com")
        pass

    scrap_pages("posts_urls.txt")

    pass
