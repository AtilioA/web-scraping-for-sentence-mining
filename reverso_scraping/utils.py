import json

def sort_json_file(filename):
    # Load the data from the JSON file into a dictionary
    with open(filename, 'r', encoding='utf8') as file:
        data = json.load(file)

    # Sort the dictionary by value and convert it back into a dictionary
    sorted_data = dict(sorted(data.items(), key=lambda item: int(item[1]), reverse=False))

    # Write the sorted data to a new JSON file
    sorted_filename = filename.replace('.json', '_sorted.json')
    with open(sorted_filename, 'w', encoding='utf8') as file:
        json.dump(sorted_data, file, ensure_ascii=False, indent=4)
