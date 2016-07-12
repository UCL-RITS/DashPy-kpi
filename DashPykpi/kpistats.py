import os
from github3 import login
import pandas as pd
import numpy as np
import codecs
import getpass
import json
import requests
from tinydb import TinyDB, Query


class KpiStats(object):
    """Gather key statstics from a repo url."""
    def __init__(self, url):
        if os.path.isfile('secret_key'):
            fn = open("secret_key")
            # Locally, with a secret_key file
            self.gh = login(token=fn.read().split()[0])
        elif os.environ.get('GHUB_API_TOKEN'):
            # On Travis? (GHUB_API_TOKEN could be set...)
            self.gh = login(token=os.environ['GHUB_API_TOKEN'])
        else:
            # Or just use username/password method
            self.gh_name = input("Username to access github with:")
            pss = getpass.getpass(prompt='Ghub pswd {0}:'.format(self.gh_name))
            self.gh = login(self.gh_name, pss)
        self.url = url
        self.repo = None
        self.stats = None
        self.db = TinyDB('tinydb_for_KPI.json')  # create new or open existing

    def __str__(self):
        print("KPI stats back-end")

    def get_repo_object_from_url(self):
        demo = 'https://github.com/<user>/<repo>'
        er1 = "Error: url should be a string in format of "
        er2 = "Error: {0} isn't valid ".format(self.url)
        assert type(self.url) == str, er1 + demo
        assert self.url.split('/')[-3] == 'github.com', er2
        user_str, repo_str = self.url.split('/')[-2:]
        self.repo = self.gh.repository(user_str, repo_str)
        return

    def get_repo_stats(self):
        contribs = [(str(contrib.author), contrib.total)
                    for contrib in self.repo.iter_contributor_statistics()]
        total = sum([user_num[1] for user_num in contribs])
        branch_count = len([branch for branch in self.repo.iter_branches()])
        self.stats = {
            'stargazers': self.repo.stargazers,
            'fork_count': self.repo.fork_count,
            'commits_by_author': contribs,
            'total_commits': total,
            'repo_owner': self.repo.owner.login,
            'repo_name': self.repo.name,
            'branches': branch_count,
            }
        return

    def add_db_row(self):
        DBfield = Query()
        results = self.db.search(DBfield.repo_name == self.repo.name)
        assert len(results) < 2, "Error, repeat entries in DB for same repo."
        if len(results) == 0:  # if no record then add the results
            self.db.insert(self.stats)
        if len(results) == 1:  # if record exists, but the user has rerun code
            eid = results[0].eid
            if results[0]['total_commits'] < self.stats['total_commits']:
                self.db.remove(eids=[eid])  # remove the old entry
                self.db.insert(self.stats)  # add the new entry
            else:
                # condition where an entry exists in DB,
                # and new stats are no diffrent (no repo changes)
                pass
        return

    def work(self, verbose=False, add_to_db=True):
        self.get_repo_object_from_url()
        self.get_repo_stats()
        # Try to deal with the timeout bug here -> retrying if no commits found
        timeout_bug = self.stats['total_commits'] < 1
        if timeout_bug:
            self.get_repo_stats()
        if add_to_db:
            self.add_db_row()
        if verbose:
            for k in sorted(self.stats):
                print(k, '-->', self.stats[k])
