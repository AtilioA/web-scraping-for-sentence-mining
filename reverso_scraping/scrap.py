import re
import requests
import itertools
from bs4 import BeautifulSoup
from google.cloud import texttospeech
from wavenet import generate_audio, generate_audio_random, get_modified_path


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

    # Removes extra whitespace
    # sentence = sentence.replace("  ", " ").strip()

    # Adds full stop if necessary
    sentence = re.sub(r"(\w+)\s*\Z", r"\1.", sentence)
    sentence = re.sub(r"(<\/u><\/b>)\s*\Z", r"\1.", sentence)

    return sentence.strip()


def crawl_page(targetURL):
    """ Crawls a page looking for links to sentences """

    pass


def scrap_page(targetURL):
    """ Scraps a single URL for sentences and generates audios using WaveNet """
    name = targetURL.split('/')[5][:-1]
    # print(name)
    with open(f"csv/{name}.csv", "w+", encoding="utf8") as card:
        # Reverso requires user-agent, otherwise will refuse the request
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

        req = requests.get(targetURL, headers=headers)
        if req.status_code == 200:
            audiosFilenames = list()
            print('Successful GET request!')

            content = req.content
            html = BeautifulSoup(content, 'html.parser')

            # Extracting french sentences
            frenchSentences = list()
            for span in html.find_all("span", lang="fr")[0:8:2]:
                frenchSentences.append(''.join(map(str, span.contents)).strip())
            frenchSentences = list(map(format_french_sentence, frenchSentences))
            # print(frenchSentences)

            # Extracting portuguese sentences
            portugueseSentences = list()
            for div in html.find_all("div", class_="trg ltr")[0:8:2]:
                for span in div.find_all("span", class_="text"):
                    portugueseSentences.append(''.join(map(str, span.contents)).strip())
            portugueseSentences = list(map(format_portuguese_sentence, portugueseSentences))
            # print(portugueseSentences)

            # Generate audios for french sentences
            # Using Google's WaveNet API
            for sentence in frenchSentences:
                # Strip sentences of html tags, otherwise will raise FileNotFoundError exception
                cleanSentence = BeautifulSoup(sentence, "lxml").text
                generate_audio_random(audiosPath, cleanSentence, language)
                audiosFilenames.append(get_modified_path(cleanSentence))

            if len(frenchSentences) != len(portugueseSentences) != len(audiosFilenames):
                print(f"Lists don't have all the same length. Output may be compromised.\n{len(frenchSentences)}, {len(portugueseSentences)}, {len(audiosFilenames)}")

            cardInfos = [x for x in itertools.chain.from_iterable(itertools.zip_longest(frenchSentences, portugueseSentences, audiosFilenames)) if x]
            for i in range(0, len(cardInfos) - 2, 3):
                card.write(f"{cardInfos[i]}^{cardInfos[i + 1]}^[sound:{cardInfos[i + 2]}.mp3]^french_reverso\n")
        else:
            print('Failed GET request.')


if __name__ == "__main__":
    audiosPath = "audios/"
    language = "fr-FR"

    # Initializing WaveNet's variables
    # Select the type of audio file
    audio_config = texttospeech.types.AudioConfig(
    audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    # Instantiates a TTS client
    client = texttospeech.TextToSpeechClient()

    # Tests
    with open("target_urls.txt", encoding="UTF8") as file:
        pages = file.readlines()

        for page in pages:
            print(f"Scraping {page}...")
            scrap_page(page)
    # scrap_page("https://context.reverso.net/traducao/frances-portugues/se+débarrasser")
    # scrap_page("https://context.reverso.net/traducao/frances-portugues/sac+à+main")
