import re


def url_encode_string(string):
    """ "Encode" string to audio URL format of Mairo's.

        Return encoded `string`.
    """

    encodedString = string.replace(" ", "-")
    encodedString = "".join(
        list(filter(lambda c: c not in "?.,!/;:’'\"", encodedString))
    )
    return re.sub("[^A-Za-z0-9\-]+", "", encodedString)
