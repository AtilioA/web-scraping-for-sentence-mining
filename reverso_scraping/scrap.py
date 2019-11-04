import requests
from bs4 import BeautifulSoup
from google.cloud import texttospeech
from wavenet import generate_audio


def crawl_page(targetURL):
    """ Crawls a page looking for links to sentences """

    pass


def scrap_page(targetURL):
    """ Scraps a single URL for sentences and generates audios using WaveNet """

    # Reverso requires user-agent, otherwise will refuse the request
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(targetURL, headers=headers)
    if req.status_code == 200:
        print('Successful GET request!')

        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Extracting french sentences
        frenchSentences = list()
        for span in html.find_all("span", lang="fr"):
            frenchSentences.append(''.join(map(str, span.contents)).strip())
        print(frenchSentences)

        # Extracting portuguese sentences
        portugueseSentences = list()
        for div in html.find_all("div", class_="trg ltr"):
            for span in div.find_all("span", class_="text"):
                portugueseSentences.append(''.join(map(str, span.contents)).strip())
        print(portugueseSentences)

        # Generate audios for french sentences
        # Using Google's WaveNet API
        for sentence in frenchSentences:
            # Strip sentences of html tags, otherwise will raise FileNotFoundError exception
            cleanSentence = BeautifulSoup(sentence, "lxml").text
            generate_audio(audiosPath, cleanSentence, language)
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

    scrap_page("https://context.reverso.net/traducao/frances-portugues/demander+conseil")
