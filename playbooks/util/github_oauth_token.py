#!/usr/bin/env python

"""
Generate a GitHub OAuth token with a particular
set of permissions.

Usage:

    github_oauth_token.py USERNAME PASSWORD [SCOPE ...]

Example:

    github_oauth_token.py jenkins_user repo:status public_repo

This will prompt the user for the password.
"""

import sys
import requests
import json
import getpass
from textwrap import dedent

USAGE = "Usage: {0} USERNAME NOTE [SCOPE ...]"


def parse_args(arg_list):
    """
    Return a dict of the command line arguments.
    Prints an error message and exits if the arguments are invalid.
    """
    if len(arg_list) < 4:
        print USAGE.format(arg_list[0])
        exit(1)

    # Prompt for the password
    password = getpass.getpass()

    return {
        'username': arg_list[1],
        'password': password,
        'note': arg_list[2],
        'scopes': arg_list[3:],
    }


def get_oauth_token(username, password, scopes, note):
    """
    Create a GitHub OAuth token with the given scopes.
    If unsuccessful, print an error message and exit.

    Returns a tuple `(token, scopes)`
    """
    params = {'scopes': scopes, 'note': note}

    response = response = requests.post(
        'https://api.github.com/authorizations',
        data=json.dumps(params),
        auth=(username, password)
    )

    if response.status_code != 201:
        print dedent("""
            Could not create OAuth token.
            HTTP status code: {0}
            Content: {1}
        """.format(response.status_code, response.text)).strip()
        exit(1)

    try:
        token_data = response.json()
        return token_data['token'], token_data['scopes']

    except TypeError:
        print "Could not parse response data."
        exit(1)

    except KeyError:
        print "Could not retrieve data from response."
        exit(1)


def main():
    arg_dict = parse_args(sys.argv)
    token, scopes = get_oauth_token(
        arg_dict['username'], arg_dict['password'],
        arg_dict['scopes'], arg_dict['note']
    )

    print "Token: {0}".format(token)
    print "Scopes: {0}".format(", ".join(scopes))


if __name__ == "__main__":
    main()
