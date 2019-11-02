import re
import requests
from bs4 import BeautifulSoup
import shutil
import itertools


def download_file(url):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        with open(f"audios/{local_filename}", 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename


def format_french_text(text):
    # Removes div tags
    text = text.replace("""<div class="post__player-title">""", '')
    text = text.replace("</div>", '').strip()

    # Replaces <strong> tags with bold and underline
    text = re.sub(r"<strong>\s*", "<u><b>", text)
    text = re.sub(r"(\W*)\s*<\/strong>", r"</u></b>\1", text)
    text = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", text)

    # Removes extra whitespace
    text = text.replace("  ", " ")

    # Adds full stop if necessary
    print(text)
    text = re.sub(r"(\w+)\Z", r"\1.\'", text)
    text = re.sub(r"(<\/u><\/b>)\Z", r"\1.", text)

    return text


def format_portuguese_text(text):
    # Removes div tags and extra whitespace
    text = re.sub(r"\s\s+", ' ', text)
    text = text.replace("""<div class="post__player-text">""", '')
    text = text.replace("</div>", '').strip()
    print(text)

    # Replaces <strong> tags with bold and underline
    text = re.sub(r"<strong>\s*", "<u><b>", text)
    text = re.sub(r"(\W*)\s*<\/strong>", r"</u></b>\1", text)
    text = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", text)

    # Adds full stop if necessary
    text = re.sub(r"(\w+)\Z", r"\1.", text)
    text = re.sub(r"(<\/u><\/b>)\Z", r"\1.", text)
    print(text)

    return text


def post_to_card(targetPost):
    name = targetPost.split('/')[3]
    with open(f"csv/{name}.csv", "w+", encoding="utf8") as card:
        frenchSentences = list()
        portugueseSentences = list()
        audiosFilenames = list()

        req = requests.get(targetPost)
        if req.status_code == 200:
            print('Successful request!')

            # Retrieving the html content
            content = req.content
            html = BeautifulSoup(content, 'html.parser')

            # Extracting french sentences
            for div in html.select('div'):
                try:
                    if "post__player-title" in div["class"]:
                        frenchSentences.append(format_french_text(str(div)))
                except KeyError:
                    pass
            # print(frenchSentences)

            # Extracting portuguese sentences
            for div in html.select('div'):
                try:
                    if "post__player-text" in div["class"]:
                        portugueseSentences.append(format_portuguese_text(str(div)))
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
            print("Failed request.")


def scrap_page(targetPage):
    req = requests.get(targetPage)
    if req.status_code == 200:
        print('Successful request!')
        # Retrieving the HTML content
        content = req.content

        # Extracting audios URLs
        html = BeautifulSoup(content, 'html.parser')
        posts = list()
        for p in html.select("a"):
            if "este-phrasal-verb" in p["href"]:
                posts.append(p["href"]) if p["href"] not in posts else posts
        for post in posts:
            print(f"Scraping {post}...")
            post_to_card(post)
    pass


if __name__ == "__main__":
    post_to_card("https://www.francesfluente.com/cest-clair/")
    pass


# TODO: Crawler to get links from "load more posts"
#        with requests.Session() as session:
#            response = session.post("https://www.francesfluente.com/wp-admin/admin-ajax.php", data={'action': 'loadmore', 'query': 'null', 'page': 1})
