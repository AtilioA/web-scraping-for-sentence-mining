import os
from google.cloud import texttospeech
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "api_key.json"


# Select the type of audio file
audio_config = texttospeech.types.AudioConfig(
    audio_encoding=texttospeech.enums.AudioEncoding.OGG_OPUS)

# Instantiates a client
client = texttospeech.TextToSpeechClient()

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


if __name__ == "__main__":
    # generate_audio("", "", "en-US")
