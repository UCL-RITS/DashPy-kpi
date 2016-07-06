import github3
import pandas as pd
import numpy as np
import codecs
import getpass
import json
import requests


class KPIGitResource(object):
    """A Github resource class. Input (one of the following):
       organization, username or repo
       If given a repo, return the output.
       Output: A dictionary with the following keys:
            Username: 'string'
            repo: 'string - URL'
            organisation: 'string' or None
            issues: int
            contributors: ['username',n]
            commits: int
            This could then be placed in a lightweight database structure -
            e.g. SQLite or TinyDB
            If an organization is given then generate a list of usernames.
            For each username find a list of repos, and find the output.
            If a username is given, then create a list of repos, and identify
            the output for each.

        NOTES: Eventually NEED TO FILTER THE REPO LIST before adding to db obj
        (UNIQUE REPOS only to avoid double counting - SET() operator?)

            """

    def __init__(self, gh_string, query_type):
        """:gh_string: a repo, username, or organization,
        :query_type: a character to indicate the type of gh_string
        either, 'r', 'u', or 'o'."""
        username = input("Github username: ")  # e.g. rc-softdev-admin
        getpss = getpass.getpass(prompt='Password for {0} '.format(username))
        self.g = ghb(username, getpss)
        self.gh_repo = None
        self.gh_org = None
        self.gh_user = None
        if query_type is 'r':
            self.gh_repo = gh_string
        elif query_type is 'o':
            self.gh_org = gh_string
        elif query_type is 'u':
            self.gh_user = gh_string
        else:
            raise ValueError("query_type must be char of 'r', 'o' or 'u'.")

    def count_commits(commits_url, _acc=0):
        """
        Count commits to a repo object
        Adapted from https://gist.github.com/gdamjan/1241096
        and Stack Overflow Question 6862770

        :Input: commit URL (api.github.com/repos/<uname>/<repo>/commits)
        :Output: integer
        """
        r = requests.get(commits_url)
        str_response = r.content.decode('utf-8')
        commits = json.loads(str_response)
        n = len(commits)
        if n == 0:
            return _acc
        link = r.headers.get('link')
        if link is None:
            return _acc + n
        next_url = find_next(r.headers['link'])
        if next_url is None:
            return _acc + n
        return count_repo_commits(next_url, _acc + n)
