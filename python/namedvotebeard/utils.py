"""Simple utils module for NamedVoteBeard."""


def get_user_name(user):
    """Returns the user's name as a string."""
    if 'last_name' in user:
        name = "{} {}".format(
            user['first_name'], user['last_name'])
    else:
        name = user['first_name']

    return name
