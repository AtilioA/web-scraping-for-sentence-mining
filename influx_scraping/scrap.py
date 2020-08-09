import re
import requests
from bs4 import BeautifulSoup
import shutil


def download_file(url):
    """ Download file from URL """

    local_filename = url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        with open(f"audios/{local_filename}", "wb") as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename


def format_english_sentence(sentence):
    """ Cleans a english sentence. Returns the new sentence """

    # Remove <strong> tags
    sentence = re.sub(r"<\/?strong>", "", sentence)

    # Manage/remove extra whitespace
    sentence = sentence.replace("&nbsp;", " ")
    sentence = sentence.replace("\xa0", " ")
    sentence = sentence.replace("  ", " ")

    # Replace <u> tags with bold and underline
    sentence = re.sub(r"<u>", "<b><u>", sentence)
    sentence = re.sub(r"<\/u>", "</b></u>", sentence)

    # Add full stop if necessary
    sentence = re.sub(r"(\w+)\s*\Z", r"\1.", sentence)
    sentence = re.sub(r"(<\/u><\/b>)\s*\Z", r"\1.", sentence)

    return sentence.strip()


def format_portuguese_sentence(sentence):
    """ Cleans a portuguese sentence. Returns the new sentence """

    # Remove <a>, <em> tags and extra whitespace
    sentence = re.sub(r"\s\s+", " ", sentence)
    sentence = re.sub(r"<\/?em>", "", sentence)
    sentence = re.sub(r"<\/?a>", "", sentence)
    # print(sentence)

    # Replace <u> tags with bold and underline
    sentence = re.sub(r"<u>", "<b><u>", sentence)
    sentence = re.sub(r"<\/u>", "</b></u>", sentence)

    # Add full stop if necessary
    sentence = re.sub(r"(\w+)\s*\Z", r"\1.", sentence)
    sentence = re.sub(r"(<\/u><\/b>)\s*\Z", r"\1.", sentence)

    return sentence.strip()


def scrap_page(targetURL):
    """ Scraps a single URL for sentences, downloading audios """

    # Extract post title from URL and use as .csv file name
    name = targetURL.split("/")[3]
    with open(f"csv/{name}.csv", "w+", encoding="utf8") as card:
        # Headers for the GET request so it doesn't get easily rejected
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
        }

        req = requests.get(targetURL, headers=headers)
        if req.status_code == 200:
            print("Successful GET request!")

            # Initialize lists for later appending
            englishSentences = list()
            portugueseSentences = list()
            audiosURLs = list()
            audioFilenames = list()

            content = req.content
            html = BeautifulSoup(content, "html.parser")

            # Extract sentences
            div = html.find("div", class_="post-content")
            # Sentences are under this div
            # divStrings = "".join(list(map(str, div)))
            # print(divStrings)
            sentencesRegex = (
                r"(?:<p.*?>(.*?)<em>(.*?)<br><span.*?><audio .*?src=(\".*?\"))"
            )
            findSentences = re.findall(
                sentencesRegex, "".join(list(map(str, div))), re.MULTILINE
            )
            for matches in findSentences:
                englishSentences.append(matches[0])
                portugueseSentences.append(matches[1])
                audiosURLs.append(matches[2])
            del findSentences

            audiosURLs = list(
                # Add domain to audio URLs
                map(lambda url: f"https://blog.influx.com.br{url}", audiosURLs)
            )
            portugueseSentences = list(
                # Clean and format Portuguese
                map(format_portuguese_sentence, portugueseSentences)
            )
            englishSentences = list(
                # Clean and format English
                map(format_english_sentence, englishSentences)
            )

            # Download audios
            for url in audiosURLs:
                print(f"Downloading {url}")
                localFilename = download_file(url)
                audioFilenames.append(localFilename)

            if len(portugueseSentences) != len(englishSentences) != len(audioFilenames):
                print(
                    f"""Lists don't have all the same length. Output may be compromised.
- in '{name}':
    ({len(englishSentences)} english sentences, {len(portugueseSentences)} portuguese sentences, {len(audioFilenames)} audio files.)"""
                )

            cardInfos = zip(englishSentences, portugueseSentences, audioFilenames)
            for sentence in cardInfos:
                card.write(
                    f"{sentence[0]}\t{sentence[1]}\t[sound:{sentence[2]}]\tenglish_influx\n"
                )  # Use TAB as separator
        else:
            print("Failed GET request.")


if __name__ == "__main__":
    # Tests
    # with open("scrap_influx.txt", "r", encoding="utf-8") as f:
    #     pages = f.readlines()

    # for page in pages:
    #     print(f"\n- Scraping {page}")
    #     scrap_page(page[:-1])  # Remove '\n' from string
