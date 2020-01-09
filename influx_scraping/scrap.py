import re
import requests
import itertools
from bs4 import BeautifulSoup


def format_english_sentence(sentence):
    """ Cleans a english sentence. Returns the new sentence """

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


def crawl_page(targetURL):
    """ Crawls a page looking for links to sentences """

    pass


def scrap_page(targetURL):
    """ Scraps a single URL for sentences, downloading audios """

    name = targetURL.split('/')[3]
    with open(f"csv/{name}.csv", "w+", encoding="utf8") as card:
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

        req = requests.get(targetURL, headers=headers)
        if req.status_code == 200:
            audiosFilenames = list()
            print('Successful GET request!')

            content = req.content
            html = BeautifulSoup(content, 'html.parser')

            # Extracting english sentences
            englishSentences = list()
            div = html.find("div", class_="post-content")
            divStrings = list(map(str, div))
            sentences = [x for x in divStrings if re.search(r"<p style=\"text-align: justify;\">", x)]
            print(sentences)
            sentences = [x.split('</strong>') for x in sentences]
            # englishSentences = [x[0] for x in sentences if "<u>" in str(x)]
            # portugueseSentences = [x[1] for x in sentences if "<u>" in str(x)]
            # print(portugueseSentences)
            # print(len(portugueseSentences))
            # print(englishSentences)
            # print(len(englishSentences))

            # print(html)
            # audios = re.findall(r"<audio src=.*\.mp3)(.*\n*<audio.*)*", str(html))
            # print(audios)
            # for audio in div.find_all("audio"):
            #     print(audio)

            # if len(englishSentences) != len(portugueseSentences) != len(audiosFilenames):
            #     print(f"Lists don't have all the same length. Output may be compromised.\n{len(englishSentences)}, {len(portugueseSentences)}, {len(audiosFilenames)}")

            # cardInfos = [x for x in itertools.chain.from_iterable(itertools.zip_longest(englishSentences, portugueseSentences, audiosFilenames)) if x]
            # for i in range(0, len(cardInfos) - 2, 3):
            #     card.write(f"{cardInfos[i]}^{cardInfos[i + 1]}^[sound:{cardInfos[i + 2]}.mp3]^english_reverso\n")
        else:
            print('Failed GET request.')


if __name__ == "__main__":
    # Tests
    scrap_page("https://blog.influx.com.br/parece-mas-nao-e-o-que-significa-it-gets-my-goat-em-ingles")
