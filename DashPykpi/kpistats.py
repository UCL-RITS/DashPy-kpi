from github3 import login
import pandas as pd
import numpy as np
import codecs
import getpass
import json
import requests


class KpiStats_dev(object):
    """Gather key statstics from a repo url.
    """
    def __init__(self, url):
        gh_name = input("Username to access github with:")
        self.gh_name
        # nb. this login can be changed to use a github token
        self.gh = login(gh_name, getpass.getpass(prompt='Ghub psswd of {0}:'.format(gh_name)))
        self.url = url
        self.repo = None
        self.stats = None

    def __str__(self):
        print("KPI stats back-end")

    def get_repo_object_from_url(self):
        demo = 'https://github.com/<user>/<repo>'
        assert type(url) == str, "Error: url should be a string in format of " + demo
        assert url.split('/')[-3] == 'github.com', "Error: {0} isn't valid ".format(url)
        user_str, repo_str = url.split('/')[-2:]
        self.repo = self.gh.repository(user_str, repo_str)
        return

    def get_repo_stats(self):
        contribs = [(str(contrib.author), contrib.total)
                    for contrib in self.repo.iter_contributor_statistics()]
        total = sum([user_num[1] for user_num in contribs])
        self.stats = {
            'name': self.repo.name,
            'stargazers': self.repo.stargazers,
            'fork_count': self.repo.fork_count,
            'commits_by_author': contribs,
            'total_commits': total,
            'repo_url': self.repo.clone_url,
            }
        return

    def work(self):
        self.get_repo_object_from_url()
        self.get_repo_stats()
        for k in sorted(self.stats):
            print(k, '-->', self.stats[k])
