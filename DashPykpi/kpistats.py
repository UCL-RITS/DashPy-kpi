from __future__ import print_function
import os
from github3 import login
import pandas as pd
import numpy as np
import codecs
import getpass
import json
import requests
from tinydb import TinyDB, Query
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.plotting import figure
from bokeh.embed import components


class KpiStats(object):
    """This class uses github3.py to gather key statistics from specified repos

    Ensure the class can log in to an authorized github account (if not only
    public repo stats can be retrieved). Two methods can be used to log in.
    Firstly using a github api token: The program will look for this in a file
    called 'secret_key' in the local folder. If this is not found the software
    will default to asking for a username and password. The class should be
    instansiated with a list of github repo url strings.

    - **paramaters**, **types** and **return**::

        :param urls: Github repo urls
        :type urls: List
        :return: KpiStats object

    :Example:

    rsts = KpiStats(['https://github.com/<user1>/<repox>',
                     'https://github.com/<user2>/<repoy>'])
    rsts.work()
    """
    def __init__(self, urls):
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
        self.urls = urls  # A list of URL strings
        self.repo = None
        self.stats = None
        self.db = TinyDB('tinydb_for_KPI.json')  # create new or open existing

    def __str__(self):
        print("KPI stats back-end")

    def get_repo_object_from_url(self, url):
        """
        function:: get_repo_object_from_url(self, url)

        Retrieves a github3.py.Repository() object from a url string in an
        authenticated session.

        :param url: url string in format 'https://github.com/<user>/<repo>'
        :rtype: Authenticated github3.py.Repository() object as self.repo()
        """
        demo = 'https://github.com/<user>/<repo>'
        er1 = "Error: url should be a string in format of "
        er2 = "Error: {0} isn't valid ".format(url)
        assert type(url) == str, er1 + demo
        assert url.split('/')[-3] == 'github.com', er2
        user_str, repo_str = url.split('/')[-2:]
        self.repo = self.gh.repository(user_str, repo_str)
        return

    def get_repo_stats(self, debug=False):
        """
        function:: KpiStats.get_repo_stats(self)

        Uses self.repo() to identify key statistics from a repository.

        :param: self
        :rtype: A dictionary object as self.stats
        """
        if debug:
            print('\nExamining stats of {0}'.format(self.repo))
        contribs = [(str(contrib.author), contrib.total)
                    for contrib in self.repo.iter_contributor_statistics()]
        total = sum([user_num[1] for user_num in contribs])
        branch_count = len([branch for branch in self.repo.iter_branches()])
        self.stats = {
            'stargazers': self.repo.stargazers,
            'fork_count': self.repo.fork_count,
            'commits_by_author': contribs,
            'num_contributors': len(contribs),
            'total_commits': total,
            'repo_owner': self.repo.owner.login,
            'repo_name': self.repo.name,
            'branches': branch_count,
            'language': self.repo.language,
            }
        return

    def add_db_row(self):
        """
        function:: KpiStats.add_db_row(self)

        Checks if there is a database and entry already present, if there isn't
        it adds a row to a database. If there is one already, it checks to see
        if the newly retrieved dictionary has updated info. If so, it removes
        the old row, and adds in the new one. If there is an error, and there
        is more than one row per repo it throws an assert error.

        :param: self
        :rtype: updates database connected to self.db
        """
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

    def clean_state(self):
        """
        function:: KpiStats.clean_state(self)

        Clean temporary data in the class before attempting to get a new repo
        object, specfically setting self.repo and self.stats to None.

        :param: self
        :rtype self.repo: None
        :rtype self.stats: None
        """
        self.repo = None
        self.stats = None

    def work(self, status=False, debug=False, verbose=False, add_to_db=True):
        """
        function:: KpiStats.work(self, status=False, debug=False,
        verbose=False, add_to_db=True)

        Main routine that handels passing single url strings to a function to
        get the repo object, and then examine statistics for each repo. It then
        writes that data to a TinyDB file. Optionally, reporting on the stats,
        progress, and execution of the called functions can be provided by
        setting the status, debug and verbose flags.
        """
        for i, url in enumerate(self.urls):
            if status:
                print("\rComplete...{0:2.0f}%".format(((i+1)/len(self.urls)
                                                       )*100.,), end="")
            self.get_repo_object_from_url(url=url)
            self.get_repo_stats(debug=debug)
            # Deal with html get timeout bug here -> retry if no commits found
            timeout_bug = self.stats['total_commits'] < 1
            if timeout_bug:
                self.get_repo_stats()
            if add_to_db:
                self.add_db_row()
            if verbose:
                for k in sorted(self.stats):
                    print(k, '-->', self.stats[k])
            self.clean_state()


class GitURLs(object):
    """Get all repo urls associated with a github account.

    Return a list of url strings as self.urls, useful during testing. In
    deployment this list will likely come directly from the Dashboard database.

    :Example:

    url_list = git_urls()
    url_list.urls[0:3]
    >['https://github.com/benlaken/Comment_BadruddinAslam2014.git',
      'https://github.com/benlaken/Composite_methods_LC13.git',
      'https://github.com/benlaken/ECCO.git']
    """
    def __init__(self):
        if os.path.isfile('secret_key'):
            fn = open("secret_key")
            # Locally, with a secret_key file
            self.gh = login(token=fn.read().split()[0])
        elif os.environ.get('GHUB_API_TOKEN'):
            # On Travis? (GHUB_API_TOKEN can be set...)
            self.gh = login(token=os.environ['GHUB_API_TOKEN'])
        else:
            # Or just use username/password method
            self.gh_name = input("Username to access github with:")
            pss = getpass.getpass(prompt='Ghub pswd {0}:'.format(self.gh_name))
            self.gh = login(self.gh_name, pss)
        self.urls = [r.clone_url.split('.git')[0]
                     for r in self.gh.iter_repos()]


class GraphKPIs(object):
    """Graph key statistics from specified repos.

    How to embed bokeh plots into Django: example at
    http://bokeh.pydata.org/en/latest/docs/user_guide/embed.html
    Essentially, insert the script and div returned into an html template and
    the div will be replaced by the plot objet. This assumes BokehJS has been
    loaded, either inline or via CDN. (See the link above to copy CDN lines.)

    - **paramaters**, **types** and **return**::

    """
    def __init__(self):

        if os.path.exists('tinydb_for_KPI.json'):
            self.db = TinyDB('tinydb_for_KPI.json')
            self.df = pd.DataFrame(self.db.all())
        else:
            raise IOError('DB file not present')

    def __str__(self):
        print("Class for graphing the output of KPIStats held in a DB.")

    def auto_title(self, x, y):
        """Plot title creator

        Automatically generate a title from two strings. The strings
        can include underscores (as they are column names from a DB), these
        are removed.

        :param x,y: string e.g. 'fork_count', 'stargazers', 'num_contributors'
        'total_commits'
        :return: string Title for plots
        """
        x = x.split('_')
        y = y.split('_')
        return ' '.join(x + ['vs.'] + y).title()

    def xy_scatter(self, x, y, ptitle=None, give_script_div=False):
        """ Create an x y scatterplot using Bokeh to insert into a webpage or
        a Jupyter notebook.

        :param x,y: string 'fork_count', 'stargazers', 'num_contributors'
        'total_commits'
        :return: Bokeh object or script and div

        :Example:
        Assuming a tinydb_for_KPI.json file exists):

        1. Creating html for Django:
        grobj = GraphKPIs()
        script, div = grobj.xy_scatter(df=, x='stargazers', y='total_commits',
        give_script_div=True)

        Then include the script and the div within the Django html template.

        2. Returning a bokeh plot object which can be displayed in a notebook.

        from bokeh.plotting import figure, show, output_notebook
        output_notebook()
        grobj = GraphKPIs()
        p = grobj.xy_scatter(x='stargazers', y='total_commits')
        show(p)
        """
        if not ptitle:
            ptitle = self.auto_title(x=x, y=y)
        df = self.df
        colormap = {
            "low": "#8400FF",
            "mid": "#FF00FF",
            "high": "#FF0088",
            "highest": "#FF0000",
                    }
        # colour points by commit numbers
        colour_list = []
        for comitnum in df.total_commits:
            if comitnum < 10:
                colour_list.append(colormap['low'])
            elif comitnum >= 10 and comitnum < 100:
                colour_list.append(colormap['mid'])
            elif comitnum >= 100 and comitnum < 1000:
                colour_list.append(colormap['high'])
            else:
                colour_list.append(colormap['highest'])
        source = ColumnDataSource(
            data=dict(
                fork_count=df.fork_count,
                repo_name=df.repo_name,
                repo_owner=df.repo_owner,
                stargazers=df.stargazers,
                num_contributors=df.num_contributors,
                total_commits=df.total_commits,
                color_by_commits=colour_list,
            )
        )
        hover = HoverTool(
                tooltips=[
                    ("Repo", "@repo_name"),
                    ("Owner", "@repo_owner"),
                    ("Stargazers", "@stargazers"),
                    ("Total commits", "@total_commits"),
                    ("Fork count", "@fork_count"),
                    ("Num. contributors", "@num_contributors"),
                ]
            )
        tools = "pan, resize, wheel_zoom, reset"
        p = figure(title=ptitle, tools=[tools, hover])
        p.xaxis.axis_label = x
        p.yaxis.axis_label = y
        p.circle(x, y, source=source, color="color_by_commits")
        if give_script_div:
            script, div = components(p)
            return script, div
        else:
            return(p)
