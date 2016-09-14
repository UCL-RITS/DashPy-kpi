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
from bokeh.charts import Area, defaults
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.charts import Area, defaults
from bokeh.plotting import figure
from bokeh.embed import components


class KpiStats(object):
    """**Gathers repo statistics from a list of github urls into a TinyDB**

    The class uses github3.py to create an authenticated Github session.
    Session is authenticaed either by:

    #. Setting up a `github-token
       <https://help.github.com/articles/creating-an-access-token-for-command-line-use/>`_
       and copying the key into a local file in the cwd called 'secret_key'.
    #. If no 'secret_key' file is detected, the user is prompted to
       enter a username and password.
    #. A github-token can be set as an environment variable
       'GHUB_API_TOKEN' (used this on Travis).

    public repo stats can be retrieved). Two methods can be used to log in.
    Firstly using a github api token: The program will look for this in a file
    called 'secret_key' in the local folder. If this is not found the software
    will default to asking for a username and password. The class should be
    instansiated with a list of github repo url strings.

    :param urls: list of url strings ['https://github.com/<user>/<repo>',]

    :returns: KpiStats() object

    :Example:

    The follwing use case shows how to feed a list of urls to KpiStats
    and then read the TinyDB object produced (by default) into pandas.

    >>> from DashPykpi.kpistats import KpiStats, GitURLs, GraphKPIs
    >>> url_fetch = GitURLs()
    >>> urls = url_fetch.urls
    # If looking through all UCL associated repos need to remove the following
    # lines:
    # urls.remove('https://github.com/UCL/ucl')
    # urls.remove('https://github.com/UCL-RITS/ucl-rits')
    >>> test = KpiStats(urls=urls)
    >>> test.work(status=True)
    >>> db = TinyDB('tinydb_for_KPI.json')
    >>> df = pd.DataFrame(db.all())
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
        print("A KPI back-end to extract data from Github.")

    def get_repo_object_from_url(self, url):
        """Get a repository object for a given github url

        Retrieves a github3.py.Repository() object from a url string under an
        authenticated session.

        :param url: a string of format 'https://github.com/<user>/<repo>'

        :returns: github3.py.Repository() object as self.repo()
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
        """Identify the statistics of an individual repo

        Examines self.repo() to identify key statistics from a repository.

        :param: self.repo()
        :rtype: A dictionary object as self.stats

        :Example:

        >>> from DashPykpi.kpistats import KpiStats
        >>> test = KpiStats(urls=["https://github.com/UCL-RITS/RSD-Dashboard"])
        >>> test.get_repo_object_from_url(url=test.urls[0])
        >>> test.get_repo_stats()
        >>> test.stats # print a dictionary of retrieved stats
        """
        if debug:
            print('\nExamining repo {0}'.format(self.repo))
        contribs = [(str(contrib.author), contrib.total)
                    for contrib in self.repo.iter_contributor_statistics()]
        total = sum([user_num[1] for user_num in contribs])
        branch_count = len([branch for branch in self.repo.iter_branches()])
        commits_over_time = [commit for commit in self.repo.iter_commit_activity()]
        weekly_commits = [week['total'] for week in commits_over_time]
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
            "weekly_commits": weekly_commits,
            }
        return

    def add_db_row(self):
        """KpiStats.add_db_row(self)

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
        """Cleans the stats and repo objects from the class between updates

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

        Main routine that handels passing single url strings to
        self.get_repo_object() to populate self.repo, and then calls
        self.get_repo_stats() to put statistics for each repo in a dictionary
        in self.stats. It then calls self.add_db_row() to write the  dic data
        to a TinyDB file, and cleans the repo and stats objects from memory.

        Optionally, it also reports on the stats, progress, and execution of
        the called functions can be provided by via a status, debug and
        verbose flags.

        :Example:

        See DashPykpi.kpistats.KpiStats()
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

    >>> from DashPykpi import GitURLs
    >>> url_list = GitURLs()
    >>> url_list.urls[0:3]
    ['https://github.com/benlaken/Comment_BadruddinAslam2014.git',
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

    How to embed bokeh plots into Django (`see example
    <http://bokeh.pydata.org/en/latest/docs/user_guide/embed.html>`_).
    Essentially, insert the script and div returned into an html template and
    the div will be replaced by the plot objet. This assumes BokehJS has been
    loaded, either inline or via CDN. (See the link above to copy CDN lines.)
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
        are removed. Possible values for x and y are 'fork_count', 'stargazers'
        , 'num_contributors' or 'total_commits'.

        :param x: string
        :param y: string
        :return: string Title for plots
        """
        x = x.split('_')
        y = y.split('_')
        return ' '.join(x + ['vs.'] + y).title()

    def xy_scatter(self, x, y, ptitle=None, give_script_div=False):
        """ Create an x y scatterplot coloured by total_commits

        Using Bokeh to insert into a webpage or a Jupyter notebook an x y
        scatter from the TinyDB. Valid inputs are column name strings for
        the numeric data in the DB, including: 'fork_count', 'stargazers',
        'num_contributors' or 'total_commits'.

        :param x: e.g. 'fork_count', 'stargazers', 'num_contributors' or 'total_commits'
        :param y: e.g. 'fork_count', 'stargazers', 'num_contributors' or 'total_commits'
        :type x: string
        :type y: string
        :return: Bokeh object or script and div string items

        :Example:

        1. Assume a database object created by KpiStats() exists and you
        wish to create the divs and script to insert into a HTML page.

        >>> from DashPykpi.kpistats import GraphKPIs
        >>> grobj = GraphKPIs()
        >>> script, div = grobj.xy_scatter(x='stargazers', y='fork_count',
        give_script_div=True)

        2. Assume a database object created by KpiStats() exists and you
        wish to plot a test figure in a Jupyter notebook.

        >>> from DashPykpi.kpistats import GraphKPIs
        >>> from bokeh.plotting import figure, show, output_notebook
        >>> grobj = GraphKPIs()
        >>> p = grobj.xy_scatter(x='stargazers', y='fork_count')
        >>> show(p)
        """
        if not ptitle:
            ptitle = self.auto_title(x=x, y=y)

        tmpdf = self.df[self.df['total_commits'] > 0]
        tmpdf = tmpdf[tmpdf['num_contributors'] < 80]
        df = tmpdf
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
        tools = "pan, resize, wheel_zoom, reset, box_select, save"
        p = figure(title=ptitle, tools=[tools, hover])
        p.xaxis.axis_label = x
        p.yaxis.axis_label = y
        p.circle(x, y, source=source, color="color_by_commits")
        if give_script_div:
            script, div = components(p)
            return script, div
        else:
            return(p)

    def weekly_activity(self, bin=None, per_repo=False, width=800, height=400,
                        give_script_div=False, verbose=False):
        """Create a stacked area plot covering the past 52 weeks of acvitity.

        Plot in the notebook (assuming a TinyDB file exists).

        bin = Number of weekly bins (if none then the resolution is weekly)

        :Example:
        >>>from bokeh.charts import show, output_notebook
        >>>from DashPykpi.kpistats import GraphKPIs
        >>>output_notebook()
        >>>bk = GraphKPIs()
        >>>show(bk.weekly_activity())
        >>>#Or, a version with all repos individually and feedback
        >>>#show(bk.weekly_activity(per_repo=True, verbose=True))
        """
        df = self.df
        defaults.width = width
        defaults.height = height
        if per_repo:
            running = 0
            num_repos = 0
            tmp_hold = {}
            for n, weekly in enumerate(df['weekly_commits']):
                if sum(weekly) > 1:
                    tmp = weekly
                    # If binning is required...
                    if bin:
                        width = bin
                        tmp = np.array(tmp)
                        tmp = tmp[:(tmp.size // width) * width].reshape(-1, width).mean(axis=1)
                        xlab = "months since now"
                    else:
                        xlab = 'weeks since now'
                    tmp_hold[df['repo_name'][n]] = tmp
                    running += sum(weekly)
                    num_repos += 1
            if verbose:
                print("{0:3,} commits, in {1} active repos (out of {2} total repos), during past 52 weeks".format(
                        running, num_repos, len(df)))
            area = Area(tmp_hold, title="Commits to all repos", legend=None,
                        stack=True, xlabel=xlab,
                        ylabel='Master repo commits/week')

            if give_script_div:
                # Iincase you want to add the graphics to a HTML template file
                script, div = components(area)
                return script, div
            else:
                return(area)
        if not per_repo:
            tmp = []
            for n, weekly in enumerate(df['weekly_commits']):
                if sum(weekly) > 1:
                    tmp.append(weekly)
            tmp = np.array(tmp)
            tmp = tmp.sum(axis=0)
            # If binning is required
            if bin:
                width = bin
                tmp = tmp[:(tmp.size // width) * width].reshape(-1, width).mean(axis=1)
                xlab = "months since now"
            else:
                xlab = "weeks since now"
            all_weekly_commits = {"All repos": tmp}
            area = Area(all_weekly_commits, title="Commits to repos",
                        legend=None, stack=True, xlabel=xlab,
                        ylabel='Master repo commits/week')
            if give_script_div:
                # Incase you want to add the graphics to an HTML template
                script, div = components(area)
                return script, div
            else:
                return(area)
