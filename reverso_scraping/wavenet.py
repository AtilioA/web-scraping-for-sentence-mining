import os
import random
from google.cloud import texttospeech
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "api_key.json"


# Select the type of audio file
audio_config = texttospeech.types.AudioConfig(
    audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)

# Instantiates a client
client = texttospeech.TextToSpeechClient()


def get_modified_path(originalPath):
    return ''.join(c for c in originalPath if c.isalpha())


def generate_audio(path, sentence, language):
    # Set the text input to be synthesized
    synthesis_input = texttospeech.types.SynthesisInput(text=sentence)

    # Build the voice request, select the language code and the ssml
    # voice gender ("neutral")
    voice = texttospeech.types.VoiceSelectionParams(
        language_code=language,
        ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(synthesis_input, voice, audio_config)

    # The response's audio_content is binary.
    with open(f'{path}{sentence}.mp3', 'wb') as out:
    # Write the response to the output audio file.
        out.write(response.audio_content)
        print(f'Audio content written to file "{path}{sentence}.mp3"')


def generate_audio_random(path, sentence, language):
    # Set the text input to be synthesized
    synthesis_input = texttospeech.types.SynthesisInput(text=sentence)

    voices = client.list_voices()
    selectedVoices = [voice.name for voice in voices.voices if (language in voice.language_codes or language in voice.language_codes) and "Standard" not in voice.name]
    # print(selectedVoices)
    selectedVoice = random.choice(selectedVoices)
    # print(selectedVoice[0:5])
    # print([voice.language_codes[0] for voice in selectedVoices])
    # selectedLanguageCode = random.choice([voice.language_codes for voice in selectedVoices])

    # Build the voice request, select the language code and the ssml
    # voice gender ("neutral")
    # genders = ["MALE", "NEUTRAL", "FEMALE"]
    # randomGender = random.choice(genders)
    # print(randomGender)
    voice = texttospeech.types.VoiceSelectionParams(
        name=selectedVoice,
        language_code=selectedVoice[0:5],
        ssml_gender=texttospeech.enums.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(synthesis_input, voice, audio_config)

    # The response's audio_content is binary.
    with open(f'{path}{get_modified_path(sentence)}.mp3', 'wb') as out:
    # Write the response to the output audio file.
        out.write(response.audio_content)
        print(f'Audio content written to file "{path}{get_modified_path(sentence)}.mp3"')


if __name__ == "__main__":
    generate_audio_random("", "", "fr-FR")
