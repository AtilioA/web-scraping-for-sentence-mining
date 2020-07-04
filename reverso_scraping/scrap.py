import re
import requests
import itertools
from bs4 import BeautifulSoup
from google.cloud import texttospeech
from wavenet import generate_audio, generate_audio_random, get_modified_path
from multiprocessing import Pool


def format_french_sentence(sentence):
    """ Cleans a french sentence. Returns the new sentence """

    # Replaces <em> tags with bold and underline
    sentence = re.sub(r"<em>\s*", "<b><u>", sentence)
    sentence = re.sub(r"(\W*)\s*<\/em>", r"</u></b>\1", sentence)
    # sentence = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", sentence)

    # Removes extra whitespace
    sentence = sentence.replace("  ", " ")

    # Adds full stop if necessary
    sentence = re.sub(r"(\w+)\s*\Z", r"\1.", sentence)
    sentence = re.sub(r"(<\/u><\/b>)\s*\Z", r"\1.", sentence)

    return sentence.strip()


def format_portuguese_sentence(sentence):
    """ Cleans a portuguese sentence. Returns the new sentence """

    # Removes <a> tags and extra whitespace
    sentence = re.sub(r"\s\s+", ' ', sentence)
    sentence = re.sub("""<a class="link_highlighted".*<em>""", "<b><u>", sentence)
    sentence = sentence.replace("</em>", "</u></b>")
    sentence = sentence.replace("</a>", '')
    # print(sentence)

    # Replaces <strong> tags with bold and underline
    sentence = re.sub(r"<strong>\s*", "<b><u>", sentence)
    sentence = re.sub(r"(\W*)\s*<\/strong>", r"</u></b>\1", sentence)
    sentence = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", sentence)

    # Adds full stop if necessary
    sentence = re.sub(r"(\w+)\s*\Z", r"\1.", sentence)
    sentence = re.sub(r"(<\/u><\/b>)\s*\Z", r"\1.", sentence)

    return sentence.strip()


def crawl_top(targetURL, ranking=False):
    """ Crawls top list or ranking page looking for links to target words/expressions """

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(targetURL, headers=headers)
    if req.status_code == 200:
        name = targetURL.split('/')[6][:-6]
        with open(f"crawl_{name}.txt", "w+", encoding="utf-8") as crawl:
            print('Successful GET request!')

            # Extracts the HTML content from the URL for parsing
            content = req.content
            html = BeautifulSoup(content, 'html.parser')

            topListDiv = html.find("div", class_="top_list")
            a = topListDiv.find_all("a")

            if ranking:
                hrefs = [a["href"] for a in a]
            else:
                # top lists have 'In Simon we trust' unwanted URL
                hrefs = [a["href"] for a in a[:-1]]

            for href in hrefs:
                crawl.write(f"{href}\n")

            return hrefs


def scrap_page(targetURL):
    """ Scraps a single URL for sentences and generates audios using WaveNet """

    name = targetURL.split('/')[5][:-1]
    with open(f"csv/{name}.csv", "w+", encoding="utf-8") as card:
        # Reverso requires user-agent, otherwise will refuse the request
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
        req = requests.get(targetURL, headers=headers)
        if req.status_code == 200:
            audiosFilenames = list()
            print('Successful GET request!')

            # Extracts the HTML content from the URL for parsing
            content = req.content
            html = BeautifulSoup(content, 'html.parser')

            # Extracts raw french sentences
            rawFrench = html.find_all("span", lang="fr")
            # Extracts raw portuguese sentences
            rawPortuguese = html.find_all("div", class_="trg ltr")

            linkedSentences = zip(rawFrench, rawPortuguese)
            sortedSentences = sorted(linkedSentences, key=lambda elem: len(elem[0].text))[0:6]

            frenchSentences = list()
            portugueseSentences = list()
            # Cleaning sentences
            for frenchElement, portugueseElement in sortedSentences:
                frenchSentence = format_french_sentence(''.join(map(str, frenchElement.contents)))

                span = portugueseElement.find("span", class_="text")
                portugueseSentence = format_portuguese_sentence(''.join(map(str, span.contents)))

                # Long sentences are hardly useful for studying
                if len(frenchSentence) > 140 or len(portugueseSentence) > 140:
                    print("Sentence is too long. Skipping it...")
                    continue  # Skip them
                else:
                    frenchSentences.append(frenchSentence)
                    portugueseSentences.append(portugueseSentence)

            if len(frenchSentences) != len(portugueseSentences):  # If parsing fails
                print(
                    f"Lists don't have all the same length. Output may be compromised.\n{len(frenchSentences)}, {len(portugueseSentences)}")

            cardInfos = list(zip(frenchSentences, portugueseSentences))
            for i in range(len(cardInfos)):  # French sentences at index 0, portuguese sentences at index 1
                # Generate audios for french sentences using Google's WaveNet API
                # Strip sentences of html tags, otherwise will raise FileNotFoundError exception
                cleanSentence = BeautifulSoup(cardInfos[i][0], "lxml").text
                generate_audio_random("audios/", cleanSentence, "fr-FR")
                audiosFilenames.append(get_modified_path(cleanSentence))

                # Write sentences and audios filenames to the .csv file
                card.write(
                    f"{cardInfos[i][0]}^{cardInfos[i][1]}^[sound:{audiosFilenames[-1]}.mp3]^french_reverso\n")
        else:
            print('Failed GET request.')


def scrap_pages_multithread(URLsTxtFile):
    with open(URLsTxtFile, encoding="utf-8") as file:
        pages = file.readlines()

    with Pool(8) as p:
        try:
            p.map(scrap_page, pages)
        except KeyboardInterrupt:
            print('Got ^C while pool mapping, terminating the pool')
            p.terminate()
            print('Terminating pool...')
            p.terminate()
            p.join()
            print('Done!')


if __name__ == "__main__":
    audiosPath = "audios/"
    language = "fr-FR"

    # Initializing WaveNet's variables
    # Select the type of audio file
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)

    # Instantiates a TTS client
    client = texttospeech.TextToSpeechClient()

    scrap_pages_multithread("crawled/1-10000/w-1-10000.txt")

    # Testing
    # with open("target_urls.txt", encoding="utf-8") as file:
    #     pages = file.readlines()

    #     for page in pages:
    #         print(f"Scraping {page}...")
    #         scrap_page(page)
    # scrap_page("https://context.reverso.net/traducao/frances-portugues/ing%C3%A9rence")
    # crawl_top("https://context.reverso.net/traducao/index/frances-portugues/w.html", ranking=True)
