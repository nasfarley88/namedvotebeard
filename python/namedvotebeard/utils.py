"""Simple utils module for NamedVoteBeard."""

import string
import re
import collections


async def get_user_name(user):
    """Returns the user's name as a string."""
    if 'last_name' in user:
        name = "{} {}".format(
            user['first_name'], user['last_name'])
    else:
        name = user['first_name']

    return name


async def make_reply_prefix(item_ind):
    """Makes the prefix for a question response. e.g. 3 -> 'c)'

    Takes the number (up to 52) of the response.

    NOTE: Above 52 is not supported (and if you have a quiz with 52 answers,
    maybe you also want to rethink your quiz?).

    """

    return "{})".format(string.ascii_letters[item_ind])


async def add_name(text, name):
    if text[-1] == ")":
        return "{} {}".format(text, name)
    else:
        return "{}, {}".format(text, name)


async def remove_name(text, name):
    retval = re.sub(r"\s{},?".format(name), "", text)
    if retval[-1] == ",":
        retval = retval[:-1]
    retval = retval.strip()
    return retval


# TODO: Make a function that recursively changes a named tuple to a dict. It's
# because namedtuples can't be pickled because the class that is created for
# them does not live in the global scope. There's an SO question on it. Using
# just dicts should work for the telegram api, so I should switch to just dicts
# where possible

def make_namedtuple_dict_recursively(obj):
    if isinstance(obj, collections.Iterable)\
       and not isinstance(obj, str):
        try:
            obj = obj._asdict()
        except AttributeError:
            pass

        try:
            return {k: make_namedtuple_dict_recursively(v)
                    for k, v in obj.items()}
        except AttributeError:
            return [make_namedtuple_dict_recursively(v) for v in obj]
    else:
        return obj


