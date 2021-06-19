import re
import urllib.parse
import functools
import requests
from bs4 import BeautifulSoup
from google.cloud import texttospeech
from wavenet import generate_audio_random, get_modified_path
from multiprocessing import Pool, cpu_count


def format_target_language_sentence(targetLanguageSentence):
    """ Cleans and formats a scraped targetLanguageSentence. Returns the new sentence """

    # Replace <em> tags with bold and underline
    targetLanguageSentence = re.sub(r"<em>\s*", "<b><u>", targetLanguageSentence)
    targetLanguageSentence = re.sub(
        r"(\W*)\s*<\/em>", r"</u></b>\1", targetLanguageSentence
    )

    # Remove extra whitespace
    targetLanguageSentence = targetLanguageSentence.replace("  ", " ")

    # Add full stop if necessary
    targetLanguageSentence = re.sub(r"(\w+)\s*\Z", r"\1.", targetLanguageSentence)
    targetLanguageSentence = re.sub(
        r"(<\/u><\/b>)\s*\Z", r"\1.", targetLanguageSentence
    )

    return targetLanguageSentence.strip()


def format_native_language_sentence(nativeLanguageSentence):
    """ Cleans and formats a scraped nativeLanguageSentence. Returns the new sentence """

    # Remove <a> tags and extra whitespace
    nativeLanguageSentence = re.sub(r"\s\s+", " ", nativeLanguageSentence)
    nativeLanguageSentence = re.sub(
        """<a class="link_highlighted".*<em>""", "<b><u>", nativeLanguageSentence
    )
    nativeLanguageSentence = nativeLanguageSentence.replace("</a>", "")
    # nativeLanguageSentence = nativeLanguageSentence.replace("</em>", "</u></b>")

    # Replace <strong> tags with bold and underline
    nativeLanguageSentence = re.sub(r"<strong>\s*", "<b><u>", nativeLanguageSentence)
    nativeLanguageSentence = re.sub(
        r"(\W*)\s*<\/strong>", r"</u></b>\1", nativeLanguageSentence
    )
    nativeLanguageSentence = re.sub(
        r"(<\/u><\/b>)(\w+)", r"\1 \2", nativeLanguageSentence
    )

    # Adds full stop if necessary
    nativeLanguageSentence = re.sub(r"(\w+)\s*\Z", r"\1.", nativeLanguageSentence)
    nativeLanguageSentence = re.sub(
        r"(<\/u><\/b>)\s*\Z", r"\1.", nativeLanguageSentence
    )

    return nativeLanguageSentence.strip()


def crawl_top(targetURL, ranking=False):
    """ Crawls top list or ranking page looking for links to target words/expressions """

    # Reverso requires user-agent, otherwise it will refuse the request
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
                # top lists have 'In Simon we trust' unwanted URL (easter egg?)
                hrefs = [a["href"] for a in a[:-1]]

            for href in hrefs:
                crawl.write(f"{href}\n")

            return hrefs


def scrap_page(targetURL, audiosPath, targetLanguage):
    """ Scraps a single URL for sentences and generates audios using WaveNet """

    # Save the word/expression from URL to use as .csv file name
    name = urllib.parse.unquote(targetURL.split("/")[5])  # [:-1]
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
            targetLanguageSentences = list()
            nativeLanguageSentences = list()

            # Extract the HTML content from the URL for parsing
            content = req.content
            html = BeautifulSoup(content, "html.parser")

            # Extract raw targetLanguage sentences
            rawTargetLanguageSentences = html.find_all(
                "span", lang=targetLanguage[:2].lower()
            )
            # Extract raw nativeLanguage sentences
            rawNativeLanguageSentences = html.find_all("div", class_="trg ltr")

            # Zip lists so we can sort sentences by target language sentence length
            linkedSentences = zip(
                rawTargetLanguageSentences, rawNativeLanguageSentences
            )
            # Keep only the 6 shortest sentences (they usually have better quality)
            sortedSentences = sorted(
                linkedSentences, key=lambda elem: len(elem[0].text)
            )[0:6]

            # Clean sentences
            for targetLanguageElement, nativeLanguageElement in sortedSentences:
                targetLanguageSentence = format_target_language_sentence(
                    "".join(map(str, targetLanguageElement.contents))
                )

                nativeLanguageSpan = nativeLanguageElement.find("span", class_="text")
                nativeLanguageSentence = format_native_language_sentence(
                    "".join(map(str, nativeLanguageSpan.contents))
                )

                # Long sentences are hardly useful for studying. Remove this if you want them.
                if (
                    len(targetLanguageSentence) > 140
                    or len(nativeLanguageSentence) > 140
                ):
                    print("Sentence is too long. Skipping it...")
                    continue
                else:
                    targetLanguageSentences.append(targetLanguageSentence)
                    nativeLanguageSentences.append(nativeLanguageSentence)

            if len(targetLanguageSentences) != len(
                nativeLanguageSentences
            ):  # If parsing fails
                print(
                    f"Lists don't have all the same length. Output may be compromised.\n{len(targetLanguageSentences)}, {len(nativeLanguageSentences)}"
                )

            cardInfos = list(zip(targetLanguageSentences, nativeLanguageSentences))
            for i in range(
                len(cardInfos)
            ):  # targetLanguage sentences at index 0, nativeLanguage sentences at index 1
                # Generate audios for targetLanguage sentences using Google's WaveNet API
                # Strip sentence of markup so we can use it as filename (otherwise will raise FileNotFoundError exception)
                cleanSentence = BeautifulSoup(cardInfos[i][0], "lxml").text
                generate_audio_random(audiosPath, cleanSentence, targetLanguage)
                audiosFilenames.append(get_modified_path(cleanSentence))

                # Write sentences and audios filenames to the .csv file, using TAB as separator
                card.write(
                    f"{cardInfos[i][0]}\t{cardInfos[i][1]}\t[sound:{audiosFilenames[-1]}.mp3]\ttargetLanguage_reverso\n"
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
    targetLanguage = "fr-FR"

    # Initializing WaveNet's variables
    # Select the type of audio file
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16
    )

    # Instantiates a TTS client
    client = texttospeech.TextToSpeechClient()

    # Crawl "top" (frequency) page
    # crawl_top("https://context.reverso.net/traducao/index/frances-portugues/w.html", ranking=True)

    # Scrap pages listed in .txt file using all CPU threads
    # scrap_pages_multithread("urls_to_scrape'_example.'txt", audiosPath, targetLanguage)
    # print("Done scraping URLs from .txt file.")

    # Examples: (remove the # to uncomment)
    # Scrap one by one from .txt file
    # with open("urls_to_scrape_example.txt", encoding="utf-8") as file:
    #     pages = file.readlines()

    #     for page in pages:
    #         print(f"Scraping {page}...")
    #         scrap_page(page)

    # Scrap one page only
    targetLanguage = "fr-FR"
    scrap_page(
        "https://context.reverso.net/translation/french-english/oui",
        audiosPath,
        targetLanguage,
    )
