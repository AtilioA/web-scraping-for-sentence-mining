import time
import json
import os
import glob
import csv
import urllib.parse
import functools
import requests
from bs4 import BeautifulSoup
from google.cloud import texttospeech
from wavenet import generate_audio_random, get_modified_path
from multiprocessing import Pool, cpu_count

from str_utils import format_target_language_sentence, format_native_language_sentence, create_prompt
from crawl import crawl_top, crawl_all
from custom_search import get_total_results
from utils import sort_json_file
from dotenv import load_dotenv
import openai

# Load .env file
load_dotenv()

# Get the API key
openai.api_key = os.getenv('OPENAI_APIKEY')

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


def process_expressions():
    # Load sorted expressions
    with open('frequency_marked_wikt_filtered.json', 'r', encoding='utf8') as f:
        expressions = json.load(f)

    # If the generated_prompts.json file does not exist or is empty, initialize an empty dictionary
    if not os.path.exists("generated_prompts.json") or os.path.getsize("generated_prompts.json") == 0:
        generated_prompts = {}
    else:
        with open("generated_prompts.json", "r", encoding='utf8') as file:
            generated_prompts = json.load(file)

    # Loop over each expression
    for expression in expressions.keys():
        # Check if this expression is already generated or if its key exists in the generated_prompts
        if ("generated" in expressions[expression] and expressions[expression]["generated"]) or expression in generated_prompts:
            continue

        # Create the prompt
        prompt = create_prompt(expression)

        # Attempt to generate the prompt
        try:
            chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], max_tokens=220, temperature=0.8).choices[0].message.content
            print(chat_completion)
            generated_prompt = json.loads(chat_completion)

            # Save the generated prompt to the dictionary
            generated_prompts[expression] = generated_prompt[expression]

            # Mark this expression as generated
            expressions[expression]["generated"] = True
            print(f"Generated prompt for {expression}")
        except Exception as e:
            print(f"Failed to generate prompt for {expression} due to {str(e)}")
            expressions[expression]["generated"] = False

        # Save the updated expressions and generated prompts to files
        with open('frequency_marked_wikt_filtered.json', 'w', encoding='utf8') as f:
            json.dump(expressions, f, ensure_ascii=False, indent=4)
        with open('generated_prompts.json', 'w', encoding='utf8') as f:
            json.dump(generated_prompts, f, ensure_ascii=False, indent=4)


def csv_to_json():
    results = {}

    # If the all_phrases.json file does not exist or is empty, initialize an empty dictionary
    if not os.path.exists("all_phrases.json") or os.path.getsize("all_phrases.json") == 0:
        results = {}
    else:
        with open("all_phrases.json", "r", encoding='utf8') as file:
            results = json.load(file)

    # Iterate over all csv files
    for csv_file in glob.glob("crawled/csv/*.csv"):
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header
            for row in reader:
                phrase = row[0]
                # Only process phrases that haven't been processed yet
                if phrase not in results:
                    # Set frequency as None as placeholder. Replace it with the actual function to calculate frequency if available.
                    # Set present_in_wiktionnaire as None as placeholder. Replace it with the actual function to check presence in Wiktionary if available.
                    results[phrase] = {"frequency": None, "present_in_wiktionnaire": None}

    # Save results after processing all phrases
    with open("all_phrases.json", "w", encoding='utf8') as file:
        json.dump(results, file, ensure_ascii=False)

def process_phrases():
    results = {}
    # If the frequency.json file does not exist or is empty, initialize an empty dictionary
    if not os.path.exists("frequency.json") or os.path.getsize("frequency.json") == 0:
        results = {}
    else:
        with open("frequency.json", "r", encoding='utf8') as file:
            results = json.load(file)

    # iterate over all csv files
    for csv_file in glob.glob("crawled/csv/*.csv"):
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header
            for row in reader:
                phrase = row[0]
                # only process phrases that haven't been processed yet
                if phrase not in results:
                    # wait 3 seconds to avoid getting blocked by Google (429 error)
                    time.sleep(3)
                    results[phrase] = get_total_results(phrase)
                    # save results after processing each phrase
                    with open("frequency.json", "w", encoding='utf8') as file:
                        json.dump(results, file, ensure_ascii=False)


if __name__ == "__main__":
    openai.api_key = os.getenv('OPENAI_APIKEY')
    # phrases = ["dans le pétrin"]
    # prompt = create_prompt(phrases)
    # print(prompt)

    process_expressions()
    # csv_to_json()


    # create a chat completion
    # chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": create_prompt(phrases)}], max_tokens=284)

    # # print the chat completion
    # print(chat_completion.choices[0].message.content)


    # Process all phrases
    # process_phrases()
    # sort_json_file("frequency.json")



# if __name__ == "__main__":
#     # Where audios should be stored, language to be used for audio generation
#     audiosPath = "audios/"
#     targetLanguage = "fr-FR"

#     # Initializing WaveNet's variables
#     # Select the type of audio file
#     audio_config = texttospeech.AudioConfig(
#         audio_encoding=texttospeech.AudioEncoding.LINEAR16
#     )

#     # Instantiates a TTS client
#     client = texttospeech.TextToSpeechClient()

#     # Crawl "top" (frequency) page
#     # crawl_top("https://context.reverso.net/traducao/index/frances-portugues/p.html", ranking=True)
#     # crawl_top("https://context.reverso.net/traducao/index/frances-portugues/p-401-800.html", onlyNames=True, ranking=False)
#     crawl_all()

#     # Scrap pages listed in .txt file using all CPU threads
#     # scrap_pages_multithread("urls_to_scrape'_example.'txt", audiosPath, targetLanguage)
#     # print("Done scraping URLs from .txt file.")

#     # Examples: (remove the # to uncomment)
#     # Scrap one by one from .txt file
#     # with open("urls_to_scrape_example.txt", encoding="utf-8") as file:
#     #     pages = file.readlines()

#     #     for page in pages:
#     #         print(f"Scraping {page}...")
#     #         scrap_page(page)

#     # Scrap one page only
#     # targetLanguage = "fr-FR"
#     # scrap_page(
#     #     "https://context.reverso.net/translation/french-english/oui",
#     #     audiosPath,
#     #     targetLanguage,
#     # )
