#
# Implementation of split.
#

import logging
import connexion

def split_get(message):
    logging.info("split: message %r, request %r, headers %r, context %r", message,
            connexion.request, connexion.request.headers, connexion.context)
    words = split_into_words(message)
    return {"words": words}

def split_into_words(message):
    return message.split()
