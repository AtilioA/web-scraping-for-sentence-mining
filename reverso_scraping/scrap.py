import requests
from bs4 import BeautifulSoup


# EVERYTHING IS WIP
# Reverso requires user-agent, otherwise will refuse the request
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
targetURL = "https://context.reverso.net/traducao/frances-portugues/demander+conseil"

req = requests.get(targetURL, headers=headers)
if req.status_code == 200:
    print('Successful GET request!')
else:
    print('Failed GET request.')
content = req.content
html = BeautifulSoup(content, 'html.parser')

frenchSentences = list()
for span in html.find_all("span", lang="fr"):
    frenchSentences.append(''.join(map(str, span.contents)).strip())
# print(frenchSentences)

portugueseSentences = list()
for div in html.find_all("div", class_="trg ltr"):
    for span in div.find_all("span", class_="text"):
        portugueseSentences.append(''.join(map(str, span.contents)).strip())
print(portugueseSentences)
