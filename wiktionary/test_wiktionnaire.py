import urllib
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Lock for safely writing to the file from multiple threads
lock = threading.Lock()

def check_expression(expression, value):
    # If this expression has already been checked, return it as is
    if value['present_in_wiktionnaire'] is not None:
        return expression, value

    # Create the URL for the expression
    url = "https://fr.wiktionary.org/wiki/" + urllib.parse.quote(expression)

    response = requests.get(url)

    # If the status code of the response is 200, the page exists
    if response.status_code == 200:
        value['present_in_wiktionnaire'] = True
    else:
        value['present_in_wiktionnaire'] = False
        print(f"Expression '{expression}' not found in Wiktionary.")

    return expression, value

def save_expression(expression, value):
    with lock:
        # Load the current data
        with open('frequency_marked.json', 'r', encoding='utf8') as f:
            data = json.load(f)

        # Update the expression's data
        data[expression] = value

        # Save back to the file
        with open('frequency_marked.json', 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def mark_expressions():
    try:
        # Try to load the marked expressions from a previous run
        with open('frequency_marked.json', 'r', encoding='utf8') as f:
            expressions = json.load(f)
            for expression, value in expressions.items():
                if type(value) is str:
                    expressions[expression] = {"frequency": expressions[expression], "present_in_wiktionnaire": None}
    except FileNotFoundError:
        # If the file doesn't exist, load the unmarked expressions
        with open('all_phrases.json', 'r', encoding='utf8') as f:
            expressions = json.load(f)
            # Initialize all expressions with None for 'present_in_wiktionnaire'
            for expression in expressions.keys():
                if type(expressions[expression]) is str:
                    expressions[expression] = {"frequency": expressions[expression], "present_in_wiktionnaire": None}

    # Create a ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(check_expression, expression, value): expression for expression, value in expressions.items()}

        for future in as_completed(future_to_url):
            expression = future_to_url[future]
            try:
                expression, value = future.result()
                save_expression(expression, value)
            except Exception as exc:
                print('%r generated an exception: %s' % (expression, exc))

mark_expressions()
