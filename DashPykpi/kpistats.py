from github3 import login
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
        self.gh = login(username, getpss)
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


def get_repo_stats(repo):
    """
    Use the guihub3.py api to gather key statstics from each repo object.
    Note, the repo is accessed via the iter_repos() method of github3.Login,
    so the session is authenticated.
    """
    contribs = [(str(contrib.author), contrib.total)
                for contrib in repo.iter_contributor_statistics()]
    total = sum([user_num[1] for user_num in contribs])
    d = {
        'name': repo.name,
        'stargazers': repo.stargazers,
        'fork_count': repo.fork_count,
        'commits_by_author': contribs,
        'total_commits': total,
        'repo_url': repo.clone_url,
        }
    return d


def iterate_over_repos(self):
    """Example to myself of how to iterate over repos collecting info..."""
    for repo in self.gh.iter_repos(type='owner'):
        tmp = self.get_repo_stats(repo)
        print(tmp)
    return
