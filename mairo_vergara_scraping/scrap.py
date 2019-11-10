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
    text = re.sub(r"<p>|<em>|<strong>", '', text)
    text = re.sub(r"<\/p>|<\/em>|<\/strong>", '', text)
    text = re.sub(r"(<br\/>\/)", '', text)

    # Replaces <span> tag with bold and underline
    # print(text)
    text = re.sub(r"<u>\s*", "<b><u>", text)
    text = re.sub(r"(\W*)\s*<\/u>", r"</u></b>\1", text)
    text = re.sub(r"<span style=\"text-decoration: underline;\">\s*", "<b><u>", text)
    text = re.sub(r"(\W*)\s*<\/span>", r"</u></b>\1", text)
    text = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", text)

    # Removes extra whitespace
    text = text.replace("  ", " ")
    text = text.replace("\n", " ")

    # Adds full stop if necessary
    text = re.sub(r"(\w+)\Z", r"\1.\'", text)
    text = re.sub(r"(<\/u><\/b>)\Z", r"\1.", text)

    return text.strip()


def format_portuguese_text(text):
    # Removes tags
    text = re.sub(r"<(\/)*p>|<(\/)*em>|<(\/)*strong>", '', text)
    text = re.sub(r"(<br(\/)*>(\/)*)", '', text)

    # Replaces tags with bold and underline
    text = re.sub(r"<u>\s*", "<b><u>", text)
    text = re.sub(r"(\W*)\s*<\/u>", r"</u></b>\1", text)
    text = re.sub(r"<span style=\"text-decoration: underline;\">\s*", "<b><u>", text)
    text = re.sub(r"(\W*)\s*<\/span>", r"</u></b>\1", text)
    text = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", text)

    # Removes extra whitespace
    text = text.replace("  ", " ")

    # Adds full stop if necessary
    text = re.sub(r"(\w+)\s*\Z", r"\1.", text)
    text = re.sub(r"(<\/u><\/b>)\s*\Z", r"\1.", text)

    return text.strip()


def post_to_card(targetPost):
    name = targetPost.split('/')[3]
    with open(f"csv/{name}.csv", "w+", encoding="utf8") as card:
        englishSentences = list()
        audiosFilenames = list()

        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
        req = requests.get(targetPost, headers=headers)
        if req.status_code == 200:
            print('Successful GET request!')
            # Retrieving the html content
            content = req.content
            html = BeautifulSoup(content, 'html.parser')

            # Extracting english sentences
            englishSentences = ["".join(x) for x in re.findall(r"(?<=<p>)(.*?)(<br\s*(\/)*>)", str(html))]
            # print(re.findall(r"(?<=<p>)(.*?)(<br\s*(\/)*>)", str(html)))
            # print(str(html))
            englishSentences = list(map(format_english_text, englishSentences))[0:-1:3]
            # print(englishSentences)

            # Extracting portuguese sentences
            portugueseSentences = re.findall(r"(?<!em>.)(<br\s*\/*\s*>\s*\n*.*)", str(html))
            portugueseSentences = list(map(format_portuguese_text, portugueseSentences))[0:-1:3]
            # print(portugueseSentences)

            # Extracting audios URLs and downloading audios
            try:
                for p in html.select('audio')[0:-1:3]:
                    print(f"Downloading {p['src']}")
                    localFilename = download_file(p['src'])
                    audiosFilenames.append(localFilename)
            except KeyError:  # Due to older posts html configuration
                for audio in html.find_all('audio', class_="wp-audio-shortcode")[0:-1:3]:
                    for a in audio.find_all('a'):
                        print(f"Downloading {a['href']}")
                        localFilename = download_file(a['href'])
                        audiosFilenames.append(localFilename)

            # Ignoring empty entries
            try:
                englishSentences.remove('')
            except ValueError:
                pass
            try:
                portugueseSentences.remove('')
            except ValueError:
                pass
            try:
                audiosFilenames.remove('')
            except ValueError:
                pass

            if len(englishSentences) != len(portugueseSentences) != len(audiosFilenames):
                print(f"Lists still don't have all the same length. Output may be compromised.\n{len(englishSentences)}, {len(portugueseSentences)}, {len(audiosFilenames)}")
                with open("failed.txt", "a+", encoding="UTF8") as file:
                    file.write(f"{targetPost}\n")
            else:
            # cardInfos = [x for x in itertools.chain.from_iterable(itertools.zip_longest(englishSentences, portugueseSentences, audiosFilenames)) if x]
                for i in range(0, len(englishSentences)):
                    try:
                        card.write(f"{englishSentences[i]}^{portugueseSentences[i]}^[sound:{audiosFilenames[i]}]^english_mairo\n")
                    except IndexError:
                        pass
        else:
            print("Failed GET request.")


def scrap_page(targetPage):
    req = requests.get(targetPage, allow_redirects=False)
    if req.status_code == 200:
        print('Successful GET request!')
        # Retrieving the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Extracting posts URLs
        posts = list()
        nPosts = 0
        for div in html.find_all("div", class_="td-module-image"):
            for a in div.find_all("a", class_="td-image-wrap"):
                posts.append(a["href"])

        # Scraping each post in the list
        print(f"{len(posts)} posts found.")
        for post in posts:
            nPosts += 1
            print(f"\nScraping post number {nPosts}: {post}...")
            post_to_card(post)
    else:
        print("Failed GET request.")
    pass


if __name__ == "__main__":
    post_to_card("https://www.mairovergara.com/grow-on-%E2%94%82o-que-significa-este-phrasal-verb/")
    # for i in range(2, 9):
    #     targetUrl = f"https://www.mairovergara.com/category/phrasal-verbs/page/{i}/"
    #     print(f"The script will scrap {targetUrl}.\n")
    #     scrap_page(targetUrl)
    pass
