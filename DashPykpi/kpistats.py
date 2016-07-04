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
            the output for each."""

    def count_commits(commits_url, _acc=0):
        """Count commits to a repo object
        Adapted from https://gist.github.com/gdamjan/1241096
        and Stack Overflow Question 6862770
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
