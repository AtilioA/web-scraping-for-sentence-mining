import os
import time
from google.cloud import texttospeech
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "wavenet.json"

# Instantiates a client
client = texttospeech.TextToSpeechClient()

# Set the text input to be synthesized
textInput = "Je suis venue demander conseil à Lucrétia."
synthesis_input = texttospeech.types.SynthesisInput(text=textInput)

# Build the voice request, select the language code and the ssml
# voice gender ("neutral")
languageInput = 'fr-FR'
voice = texttospeech.types.VoiceSelectionParams(
    language_code=languageInput,
    ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)

# Select the type of audio file
audio_config = texttospeech.types.AudioConfig(
    audio_encoding=texttospeech.enums.AudioEncoding.MP3)

# Perform the text-to-speech request on the text input with the selected
# voice parameters and audio file type
response = client.synthesize_speech(synthesis_input, voice, audio_config)

# Placeholder for file naming.
date = str(time.strftime("%H.%M.%S"))

# The response's audio_content is binary.
with open(f'output{date}.mp3', 'wb') as out:
    # Write the response to the output audio file.
    out.write(response.audio_content)
    print(f'Audio content written to file "output{date}.mp3"')
