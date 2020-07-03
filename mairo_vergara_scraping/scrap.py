from pathlib import Path
import re
import logging
import requests
from bs4 import BeautifulSoup
import shutil


def download_file(url):
    """ Download file from URL """

    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        with open(f"audios/{local_filename}", 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename


def format_english_text(text):
    # print(text)

    # Remove tags
    text = re.sub(r"<p>|<em>|<strong>|/$", '', text)
    text = re.sub(r"<\/p>|<\/em>|<\/strong>", '', text)
    text = re.sub(r"(<br\/>\/)", '', text)

    # Replace <span> tag with bold and underline
    # print(text)
    text = re.sub(r"<u>\s*", "<b><u>", text)
    text = re.sub(r"(\W*)\s*<\/u>", r"</u></b>\1", text)
    text = re.sub(
        r"<span style=\"text-decoration: underline;\">\s*", "<b><u>", text)
    text = re.sub(r"(\W*)\s*<\/span>", r"</u></b>\1", text)
    text = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", text)

    # Remove extra whitespace
    text = text.replace("  ", " ")
    text = text.replace("\n", " ")

    # Add full stop if necessary
    text = re.sub(r"(\w+)\Z", r"\1.\'", text)
    text = re.sub(r"(<\/u><\/b>)\Z", r"\1.", text)

    return text.strip()


def format_portuguese_text(text):
    # Remove tags
    text = re.sub(r"<(\/)*p>|<(\/)*em>|<(\/)*strong>", '', text)
    text = re.sub(r"(<br(\/)*>(\/)*)", '', text)

    # Replace tags with bold and underline
    text = re.sub(r"<u>\s*", "<b><u>", text)
    text = re.sub(r"(\W*)\s*<\/u>", r"</u></b>\1", text)
    text = re.sub(
        r"<span style=\"text-decoration: underline;\">\s*", "<b><u>", text)
    text = re.sub(r"(\W*)\s*<\/span>", r"</u></b>\1", text)
    text = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", text)

    # Remove extra whitespace
    text = text.replace("  ", " ")

    # Add full stop if necessary
    text = re.sub(r"(\w+)\s*\Z", r"\1.", text)
    text = re.sub(r"(<\/u><\/b>)\s*\Z", r"\1.", text)

    return text.strip()


def post_to_card(targetPost):
    name = targetPost.split('/')[3]
    with open(f"csv/{name}.csv", "w+", encoding="utf8") as card:
        englishSentences = list()
        audiosURLs = list()
        audiosFilenames = list()

        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
        req = requests.get(targetPost, headers=headers)
        if req.status_code == 200:
            print('Successful GET request!')

            # Retrieve HTML content
            content = req.content
            html = BeautifulSoup(content, 'html.parser')

            # Extract english sentences
            englishSentences = ["".join(x) for x in re.findall(
                r"(?:<p.*?>)(.*?)(?:<br\s*(\/)*>)/?", str(html))]
            englishSentences = list(map(format_english_text, englishSentences))
            # print(englishSentences)

            # Extract portuguese sentences
            portugueseSentences = re.findall(
                r"(?<!em>.)(<br\s*\/*\s*>\s*\n*.*)", str(html))
            portugueseSentences = list(
                map(format_portuguese_text, portugueseSentences))
            # print(portugueseSentences)

            # Extract audios URLs and downloading audios
            try:
                for p in html.select('audio'):
                    print(f"Downloading {p['src']}")
                    # localFilename = download_file(p['src'])
                    audiosURLs.append(p['src'])
            except KeyError:  # Due to older posts html configuration
                for audio in html.find_all('audio', class_="wp-audio-shortcode"):
                    for a in audio.find_all('a'):
                        audiosURLs.append(a['href'])

            # Ignore empty entries
            try:
                englishSentences.remove('')
            except ValueError:
                pass
            try:
                portugueseSentences.remove('')
            except ValueError:
                pass
            try:
                audiosURLs.remove('')
            except ValueError:
                pass

            print(len(englishSentences), len(portugueseSentences), len(audiosURLs))
            # Try to adjust uneven lists
            while len(englishSentences) != len(audiosURLs) or len(audiosURLs) != len(portugueseSentences):
                print(
                    f"Lists don't have all the same length. Output may be compromised. {len(englishSentences)} english sentences, {len(portugueseSentences)} portuguese sentences, {len(audiosURLs)} audio files.")
                if len(englishSentences) > len(audiosURLs):
                    englishSentences = englishSentences[1:]
                elif len(portugueseSentences) > len(audiosURLs):
                    portugueseSentences = portugueseSentences[1:]
                else:
                    audiosURLs = audiosURLs[1:]
                failedLogger.error(targetPost)

            # Get every third sentence (adjusting this will get more or less sentences from the page)
            englishSentences = englishSentences[0:-1:3]
            portugueseSentences = portugueseSentences[0:-1:3]
            audiosURLs = audiosURLs[0:-1:3]

            # Download audio files
            for audioFilename in audiosURLs:
                print(f"Downloading {audioFilename}")
                audiosFilenames.append(download_file(audioFilename))

            # Write data to CSV
            for i in range(0, len(englishSentences)):
                try:
                    card.write(
                        f"{englishSentences[i]}^{portugueseSentences[i]}^[sound:{audiosFilenames[i]}]^english_mairo\n")
                except IndexError:
                    print(f"Failed writing data do CSV.")
                    pass
        else:
            print("Failed GET request.")


def scrap_page(targetPage):
    req = requests.get(targetPage, allow_redirects=False)
    if req.status_code == 200:
        print('Successful GET request!')
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Extract posts URLs
        posts = list()
        nPosts = 0
        for div in html.find_all("div", class_="td-module-image"):
            for a in div.find_all("a", class_="td-image-wrap"):
                posts.append(a["href"])

        with open('posts.txt', 'a+') as f:
            for post in posts:
                f.write(f"{post}\n")

        # Scrape each post in the list
        print(f"{len(posts)} posts found.")
        for post in posts:
            nPosts += 1
            print(f"\nScraping post number {nPosts}: {post}...")
            post_to_card(post)
    else:
        print("Failed GET request.")


def scrap_pages_txt(txtFilePath):
    with open(Path(txtFilePath), 'r', encoding="utf-8") as f:
        pages = f.readlines()

    for page in pages:
        post_to_card(page[:-1])  # Remove '\n' from string


if __name__ == "__main__":
    # Logger for debugging purposes; logging HTTPS requests, etc
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        filename='requests.log',
                        level=logging.DEBUG)
    logging.FileHandler("requests.log", mode='w')

    # Logger for failed parsings
    failedLogger = logging.getLogger("failed")
    failedLogger.setLevel(logging.ERROR)
    failedLogger_file_handler = logging.FileHandler("failed.log")
    failedLogger_file_handler.setLevel(logging.ERROR)
    failedLogger.addHandler(failedLogger_file_handler)

    # scrap_pages_txt('posts.txt')
    
    # scrap_page("https://www.mairovergara.com/category/como-se-diz-em-ingles/page/2/")
    # targetUrl = f"https://www.mairovergara.com/category/phrasal-verbs/page/{2}/"
    # for i in range(2, 11):
    # targetUrl = f"https://www.mairovergara.com/category/como-se-diz-em-ingles/page/{i}/"
    # print(f"The script will scrap {targetUrl}.\n")
    # scrap_for_urls(targetUrl)
