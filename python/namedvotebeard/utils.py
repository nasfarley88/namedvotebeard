"""Simple utils module for NamedVoteBeard."""

import string


def get_user_name(user):
    """Returns the user's name as a string."""
    if 'last_name' in user:
        name = "{} {}".format(
            user['first_name'], user['last_name'])
    else:
        name = user['first_name']

    return name


def make_reply_prefix(item_ind):
    """Makes the prefix for a question response. e.g. 3 -> 'c)'

    Takes the number (up to 52) of the response.

    NOTE: Above 52 is not supported (and if you have a quiz with 52 answers,
    maybe you also want to rethink your quiz?).

    """

    return "{})".format(string.ascii_letters[item_ind])
