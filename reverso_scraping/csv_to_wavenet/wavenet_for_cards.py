import sys
sys.path.append("..")

import pandas as pd
from wavenet import generate_audio_random, get_modified_path


if __name__ == "__main__":
    with open("new_cards.tsv", "w+", encoding="utf8") as f:
        old = pd.read_csv("exported_cards.txt", sep='\t')
        print(old)

        audiosFilenames = []

        allFields = list(zip(old["French"], old["English"], old["Target"], old["Tags"]))
        # print(allFields)

        for french, english, target, tags in allFields:
            generate_audio_random("audios/", french, "fr-FR")
            audioFilename = get_modified_path(french)
            audiosFilenames.append(audioFilename)

            print(french)
            print(english)
            print(audioFilename)

            if pd.isnull(target):
                target = ''
            if pd.isnull(tags):
                tags = ''

            print(f"Writing info to file...")
            f.write(f"{french}\t{english}\t[sound:{audioFilename}.mp3]\t{target}\t{tags}\n")
