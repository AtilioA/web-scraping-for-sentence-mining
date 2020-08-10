import re
import functools
import requests
from bs4 import BeautifulSoup
from google.cloud import texttospeech
from wavenet import generate_audio_random, get_modified_path
from multiprocessing import Pool, cpu_count


def format_french_sentence(frenchSentence):
    """ Cleans and formats a scraped french sentence. Returns the new sentence """

    # Replace <em> tags with bold and underline
    frenchSentence = re.sub(r"<em>\s*", "<b><u>", frenchSentence)
    frenchSentence = re.sub(r"(\W*)\s*<\/em>", r"</u></b>\1", frenchSentence)

    # Remove extra whitespace
    frenchSentence = frenchSentence.replace("  ", " ")

    # Add full stop if necessary
    frenchSentence = re.sub(r"(\w+)\s*\Z", r"\1.", frenchSentence)
    frenchSentence = re.sub(r"(<\/u><\/b>)\s*\Z", r"\1.", frenchSentence)

    return frenchSentence.strip()


def format_portuguese_sentence(portuguesesSentence):
    """ Cleans and formats a scraped portuguese sentence. Returns the new sentence """

    # Remove <a> tags and extra whitespace
    portuguesesSentence = re.sub(r"\s\s+", " ", portuguesesSentence)
    portuguesesSentence = re.sub(
        """<a class="link_highlighted".*<em>""", "<b><u>", portuguesesSentence
    )
    portuguesesSentence = portuguesesSentence.replace("</a>", "")
    # portuguesesSentence = portuguesesSentence.replace("</em>", "</u></b>")

    # Replace <strong> tags with bold and underline
    portuguesesSentence = re.sub(r"<strong>\s*", "<b><u>", portuguesesSentence)
    portuguesesSentence = re.sub(
        r"(\W*)\s*<\/strong>", r"</u></b>\1", portuguesesSentence
    )
    portuguesesSentence = re.sub(r"(<\/u><\/b>)(\w+)", r"\1 \2", portuguesesSentence)

    # Adds full stop if necessary
    portuguesesSentence = re.sub(r"(\w+)\s*\Z", r"\1.", portuguesesSentence)
    portuguesesSentence = re.sub(r"(<\/u><\/b>)\s*\Z", r"\1.", portuguesesSentence)

    return portuguesesSentence.strip()


def crawl_top(targetURL, ranking=False):
    """ Crawls top list or ranking page looking for links to target words/expressions """

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
    }

    req = requests.get(targetURL, headers=headers)
    if req.status_code == 200:
        name = targetURL.split("/")[6][:-6]
        with open(f"crawl_{name}.txt", "w+", encoding="utf-8") as crawl:
            print("Successful GET request!")

            # Extract the HTML content from the URL for parsing
            content = req.content
            html = BeautifulSoup(content, "html.parser")

            topListDiv = html.find("div", class_="top_list")
            a = topListDiv.find_all("a")

            # Ex: /index/frances-portugues/w.html
            if ranking:
                hrefs = [a["href"] for a in a]
            else:  # Ex: /index/frances-portugues/w-1-300.html
                # top lists have 'In Simon we trust' unwanted URL (???)
                hrefs = [a["href"] for a in a[:-1]]

            for href in hrefs:
                crawl.write(f"{href}\n")

            return hrefs


def scrap_page(targetURL, audiosPath, targetLanguage):
    """ Scraps a single URL for sentences and generates audios using WaveNet """

    # Save the word/expression from URL to use as .csv file name
    name = targetURL.split("/")[5][:-1]
    with open(f"csv/{name}.csv", "w+", encoding="utf-8") as card:
        # Reverso requires user-agent, otherwise it will refuse the request
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
        }

        req = requests.get(targetURL, headers=headers)
        if req.status_code == 200:
            print("Successful GET request!")

            # Initialize lists for later appending
            audiosFilenames = list()
            frenchSentences = list()
            portugueseSentences = list()

            # Extract the HTML content from the URL for parsing
            content = req.content
            html = BeautifulSoup(content, "html.parser")

            # Extract raw french sentences
            rawFrench = html.find_all("span", lang="fr")
            # Extract raw portuguese sentences
            rawPortuguese = html.find_all("div", class_="trg ltr")

            # Zip lists so we can sort sentences by target language sentence length
            linkedSentences = zip(rawFrench, rawPortuguese)
            # Keep only the 6 shortest sentences (they usually have better quality)
            sortedSentences = sorted(
                linkedSentences, key=lambda elem: len(elem[0].text)
            )[0:6]

            # Clean sentences
            for frenchElement, portugueseElement in sortedSentences:
                frenchSentence = format_french_sentence(
                    "".join(map(str, frenchElement.contents))
                )

                span = portugueseElement.find("span", class_="text")
                portugueseSentence = format_portuguese_sentence(
                    "".join(map(str, span.contents))
                )

                # Long sentences are hardly useful for studying. Remove this if you want them.
                if len(frenchSentence) > 140 or len(portugueseSentence) > 140:
                    print("Sentence is too long. Skipping it...")
                    continue
                else:
                    frenchSentences.append(frenchSentence)
                    portugueseSentences.append(portugueseSentence)

            if len(frenchSentences) != len(portugueseSentences):  # If parsing fails
                print(
                    f"Lists don't have all the same length. Output may be compromised.\n{len(frenchSentences)}, {len(portugueseSentences)}"
                )

            cardInfos = list(zip(frenchSentences, portugueseSentences))
            for i in range(
                len(cardInfos)
            ):  # French sentences at index 0, portuguese sentences at index 1
                # Generate audios for french sentences using Google's WaveNet API
                # Strip sentence of markup so we can use it as filename (otherwise will raise FileNotFoundError exception)
                cleanSentence = BeautifulSoup(cardInfos[i][0], "lxml").text
                generate_audio_random(audiosPath, cleanSentence, targetLanguage)
                audiosFilenames.append(get_modified_path(cleanSentence))

                # Write sentences and audios filenames to the .csv file, using TAB as separator
                card.write(
                    f"{cardInfos[i][0]}\t{cardInfos[i][1]}\t[sound:{audiosFilenames[-1]}.mp3]\tfrench_reverso\n"
                )
        else:
            print("Failed GET request.")


def scrap_pages_multithread(URLsTxtFile, audiosPath, targetLanguage):
    # Load all URLs to a list
    with open(URLsTxtFile, encoding="utf-8") as file:
        pages = file.readlines()

    # Lower this if you don't want to use all your CPU threads
    nThreads = cpu_count()
    print(f"Running with {nThreads} threads.")

    with Pool(nThreads) as p:
        try:
            # Scrap pages synchronously
            p.map(
                functools.partial(
                    scrap_page, audiosPath=audiosPath, targetLanguage=targetLanguage
                ),
                pages,
            )
        except KeyboardInterrupt:  # Press Ctrl + C to stop execution at any time
            print("Got ^C while pool mapping, terminating the pool")
            p.terminate()
            print("Terminating pool...")
            p.terminate()
            p.join()
            print("Done!")


if __name__ == "__main__":
    # Where audios should be stored, language to be used for audio generation
    audiosPath = "audios/"
    targetLanguage = "de-DE"

    # Initializing WaveNet's variables
    # Select the type of audio file
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16
    )

    # Instantiates a TTS client
    client = texttospeech.TextToSpeechClient()

    # Scrap pages listed in .txt file using all CPU threads
    # scrap_pages_multithread("urls_to_scrape_test.txt", audiosPath, targetLanguage)

    # Scrap one by one from .txt file
    # with open("urls_to_scrape_test.txt", encoding="utf-8") as file:
    #     pages = file.readlines()

    #     for page in pages:
    #         print(f"Scraping {page}...")
    #         scrap_page(page)

    # Scrap one page only
    scrap_page(
        "https://context.reverso.net/traducao/alemao-ingles/ich",
        audiosPath,
        targetLanguage,
    )

    # Crawl top (by frequency)
    # crawl_top("https://context.reverso.net/traducao/index/frances-portugues/w.html", ranking=True)
