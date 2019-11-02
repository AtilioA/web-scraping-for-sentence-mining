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
    # Removes tags
    text = re.sub(r"<p>|<em>|<strong>", '', text).strip()
    text = re.sub(r"(<br\/>\/)", '', text)

    # Replaces <span> tag with bold and underline
    text = re.sub(r"<span style=\"text-decoration: underline;\">\s*", "<b><u>", text)
    text = re.sub(r"(\W*)\s*<\/span>", r"</u></b>\1", text)
    text = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", text)

    # Removes extra whitespace
    text = text.replace("  ", " ")

    # Adds full stop if necessary
    text = re.sub(r"(\w+)\Z", r"\1.\'", text)
    text = re.sub(r"(<\/u><\/b>)\Z", r"\1.", text)

    return text


def format_portuguese_text(text):
    # Removes tags
    text = re.sub(r"<(\/)*p>|<(\/)*em>|<(\/)*strong>", '', text).strip()
    text = re.sub(r"(<br(\/)*>(\/)*)", '', text)

    # Replaces <span> tag with bold and underline
    text = re.sub(r"<span style=\"text-decoration: underline;\">\s*", "<b><u>", text)
    text = re.sub(r"(\W*)\s*<\/span>", r"</u></b>\1", text)
    text = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", text)

    # Removes extra whitespace
    text = text.replace("  ", " ")

    # Adds full stop if necessary
    text = re.sub(r"(\w+)\s*\Z", r"\1.", text)
    text = re.sub(r"(<\/u><\/b>)\s*\Z", r"\1.", text)

    return text


def post_to_card(targetPost):
    name = targetPost.split('/')[3]
    with open(f"csv/{name}.csv", "w+", encoding="utf8") as card:
        englishSentences = list()
        audiosFilenames = list()

        req = requests.get(targetPost)
        if req.status_code == 200:
            print('Successful request!')
            # Retrieving the html content
            content = req.content
            html = BeautifulSoup(content, 'html.parser')

            # Extracting english sentences
            englishSentences = ["".join(x) for x in re.findall(r"(<p>)(.*?)(<br(\/)*>)", str(html))]
            englishSentences = list(map(format_english_text, englishSentences))
            # print(englishSentences)

            # Extracting portuguese sentences
            portugueseSentences = re.findall(r"(<br\/>.*)", str(html))
            portugueseSentences = list(map(format_portuguese_text, portugueseSentences))
            # print(portugueseSentences)

            # Extracting audios URLs and downloading audios
            for p in html.select('audio'):
                print(f"Downloading {p['src']}")
                localFilename = download_file(p['src'])
                audiosFilenames.append(localFilename)

            if len(englishSentences) != len(portugueseSentences) != len(audiosFilenames):
                print("Lists don't have all the same length. Output may be compromised.\n")
            cardInfos = [x for x in itertools.chain.from_iterable(itertools.zip_longest(englishSentences, portugueseSentences, audiosFilenames)) if x]
            # print(cardInfos)
            for i in range(0, len(cardInfos) - 2, 3):
                card.write(f"{cardInfos[i]}|{cardInfos[i + 1]}|[sound:{cardInfos[i + 2]}]|english_mairo\n")
        else:
            print("Failed request.")


def scrap_page(targetPage):
    req = requests.get(targetPage)
    if req.status_code == 200:
        print('Successful request!')
        # Retrieving the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        posts = list()
        nPosts = 0
        for p in html.select("a"):
            if "este-phrasal-verb" in p["href"]:
                posts.append(p["href"]) if p["href"] not in posts else posts
        print(f"{len(posts)} posts found.")
        for post in posts:
            nPosts += 1
            print(f"Scraping post number {nPosts}: {post}...")
            post_to_card(post)
    pass


if __name__ == "__main__":
    # post_to_card("https://www.mairovergara.com/act-as-o-que-significa-este-phrasal-verb/")
    targetUrl = "https://www.mairovergara.com/category/phrasal-verbs/"
    print(f"The script will scrap {targetUrl}.\n")
    scrap_page(targetUrl)
    pass
