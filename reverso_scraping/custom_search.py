import os
import requests
import json

os.environ["GOOGLE_API_KEY"] = # Insert your API key here
os.environ["FRENCH_SEARCH_ENGINE_ID"] = # Insert your search engine ID here

def google_search(search_term):
    # Get API key and search engine ID from environment variables
    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("FRENCH_SEARCH_ENGINE_ID")

    # print(f"API Key: {api_key}")
    # print(f"Search Engine ID: {search_engine_id}")

    # Specify search URL and parameters
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": search_term
    }

    # Send request to Google Custom Search API and get response
    response = requests.get(url, params=params)

    # Raise an exception if the request was unsuccessful
    if response.status_code != 200:
        raise Exception(f"Request to Google Custom Search API failed with status code {response.status_code}")

    # Parse JSON response
    data = json.loads(response.text)

    return data


def get_total_results(q: str):
    data = google_search(q)
    return data["searchInformation"]["totalResults"]

if __name__ == "__main__":
    q = '"ministre des transports"'
    print(get_total_results(q))
