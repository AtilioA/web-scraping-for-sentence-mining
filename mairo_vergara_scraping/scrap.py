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


def format_english_text(text):
    text = text.replace("<em>", '')
    text = text.replace("<span style=\"text-decoration: underline;\">", '<b><u>')
    text = text.replace("</span>", '</b></u>')
    text = text.replace("<br/></em>", '')
    return text


def format_portuguese_text(text):
    text = text.replace("</em>", '')
    text = text.replace("<em>", '')
    text = text.replace("<strong>", '')
    text = text.replace("</strong>", '')
    text = text.replace("<br/>", '')
    text = text.replace("</p>", '')
    text = text.replace("<span style=\"text-decoration: underline;\">", '<b><u>')
    text = text.replace("</span>", '</u></b>')
    return text


def post_to_card(targetPost):
    name = targetPost.split('/')[3]
    with open(f"{name}.csv", "w+", encoding="utf8") as card:
        englishSentences = list()
        audiosFilenames = list()

        req = requests.get(targetPost)
        if req.status_code == 200:
            print('Successful request!')
            # Retrieving the html content
            content = req.content

            # Extracting audios URLs
            html = BeautifulSoup(content, 'html.parser')
            # Downloading audios
            for p in html.select('audio'):
                print(f"Downloading {p['src']}...")
                localFilename = download_file(p['src'])
                audiosFilenames.append(localFilename)

            # Extracting english sentences
            for p in html.select('strong em'):
                p = format_english_text(str(p))
                englishSentences.append(p)
            # print(englishSentences)

            # Extracting portuguese sentences
            # portugueseSentences = re.findall(r"(<br\/><\/em><\/strong>.*|<\/strong><em><br\/>.*|<br\/><\/em><\/strong><em>).*|<br\/><\/em><\/strong><em>.*|<\/em><br\/><\/strong><em>.*", str(html))
            portugueseSentences = re.findall(r"(<br\/>.*)", str(html))
            portugueseSentences = list(map(format_portuguese_text, portugueseSentences))
            # print(portugueseSentences)

            cardInfos = [x for x in itertools.chain.from_iterable(itertools.zip_longest(englishSentences, portugueseSentences, audiosFilenames)) if x]
            # print(cardInfos)
            for i in range(0, len(cardInfos) - 3, 3):
                card.write(f"{cardInfos[i]};{cardInfos[i + 1]};[sound:{cardInfos[i + 2]}];\n")


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
    post_to_card("https://www.mairovergara.com/water-down-o-que-significa-este-phrasal-verb/")
    targetUrl = "https://www.mairovergara.com/category/phrasal-verbs/"
    print(f"The script will scrap {targetUrl}.")
    scrap_page(targetUrl)
    pass
