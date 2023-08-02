import re

def format_target_language_sentence(targetLanguageSentence):
    """ Cleans and formats a scraped targetLanguageSentence. Returns the new sentence """

    # Replace <em> tags with bold and underline
    targetLanguageSentence = re.sub(r"<em>\s*", "<b><u>", targetLanguageSentence)
    targetLanguageSentence = re.sub(
        r"(\W*)\s*<\/em>", r"</u></b>\1", targetLanguageSentence
    )

    # Remove extra whitespace
    targetLanguageSentence = targetLanguageSentence.replace("  ", " ")

    # Add full stop if necessary
    targetLanguageSentence = re.sub(r"(\w+)\s*\Z", r"\1.", targetLanguageSentence)
    targetLanguageSentence = re.sub(
        r"(<\/u><\/b>)\s*\Z", r"\1.", targetLanguageSentence
    )

    return targetLanguageSentence.strip()


def format_native_language_sentence(nativeLanguageSentence):
    """ Cleans and formats a scraped nativeLanguageSentence. Returns the new sentence """

    # Remove <a> tags and extra whitespace
    nativeLanguageSentence = re.sub(r"\s\s+", " ", nativeLanguageSentence)
    nativeLanguageSentence = re.sub(
        """<a class="link_highlighted".*<em>""", "<b><u>", nativeLanguageSentence
    )
    nativeLanguageSentence = nativeLanguageSentence.replace("</a>", "")
    # nativeLanguageSentence = nativeLanguageSentence.replace("</em>", "</u></b>")

    # Replace <strong> tags with bold and underline
    nativeLanguageSentence = re.sub(r"<strong>\s*", "<b><u>", nativeLanguageSentence)
    nativeLanguageSentence = re.sub(
        r"(\W*)\s*<\/strong>", r"</u></b>\1", nativeLanguageSentence
    )
    nativeLanguageSentence = re.sub(
        r"(<\/u><\/b>)(\w+)", r"\1 \2", nativeLanguageSentence
    )

    # Adds full stop if necessary
    nativeLanguageSentence = re.sub(r"(\w+)\s*\Z", r"\1.", nativeLanguageSentence)
    nativeLanguageSentence = re.sub(
        r"(<\/u><\/b>)\s*\Z", r"\1.", nativeLanguageSentence
    )

    return nativeLanguageSentence.strip()

def create_prompt(phrases):
    # Start of the prompt
    prompt = "Come up with two different sentences in French for each expression in the following list, and provide a explanation using only French (monolingual translation/definition); feel free to add HTML tags such as <b>, <i>, <u> whenever appropriate, while warning about potential misuses if applicable. Also provide equivalent expressions (not full sentences) in PT_BR and EN_US:\n"

    # Add each phrase to the prompt
    if type(phrases) == list:
        for phrase in phrases:
            prompt += phrase + "\n"
    else:
        prompt += phrases + "\n"

    # End of the prompt
    prompt += "\nAnswer in a single valid JSON of this format: {expressionName: { sentences: [], explanation: \"\", english_equivalent: [""], portuguese_equivalent: [""]}. Add more sentences in the same JSON entry if the expression has more than two meanings."

    return prompt
