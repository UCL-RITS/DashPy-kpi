from __future__ import print_function
from DashPykpi.kpistats import KpiStats, GitURLs, GraphKPIs
import os
import sys
from pytest import raises


def test_public_repo_access():
    if os.path.isfile('tinydb_for_KPI.json'):
        os.remove('tinydb_for_KPI.json')
    urls = ["https://github.com/benlaken/Comment_BadruddinAslam2014"]
    test = KpiStats(urls=urls)
    test.work()
    tmp = test.db.all()  # get the results from the DB object
    em1 = "Error, insufficent commits in public repo"
    assert tmp[0]['total_commits'] > 20, em1


def test_private_repo_access():
    if os.path.isfile('tinydb_for_KPI.json'):
        os.remove('tinydb_for_KPI.json')
    urls = ["https://github.com/UCL-RITS/RSD-Dashboard"]
    test = KpiStats(urls=urls)
    test.work()
    tmp = test.db.all()  # get the results from the DB object
    em1 = "Error, insufficent commits in privte repo"
    assert tmp[0]['total_commits'] > 1000, em1


def test_adds_rows_to_db():
    """Test the database file is created and populated appropriatley."""
    if os.path.isfile('tinydb_for_KPI.json'):
        os.remove('tinydb_for_KPI.json')
    urls = ["https://github.com/UCL-RITS/RSD-Dashboard",
            "https://github.com/benlaken/Comment_BadruddinAslam2014",
            "https://github.com/benlaken/fispy"]
    test = KpiStats(urls=urls)
    test.work()
    db_rows = test.db.all()
    assert len(db_rows) == 3, "Error, incorrect number of rows in DB"


def test_GitURLs_populates():
    """Test that the GitURLs class, meant for development, retrieves data."""
    url_list = GitURLs()
    assert len(url_list.urls) > 0, "Error, GitURLs() class not retrieving urls"


def test_script_div_created():
    """Check valid div and JS string objects are returned from bokeh"""
    grobj = GraphKPIs()
    script, div = grobj.xy_scatter(x='stargazers', y='fork_count',
                                   give_script_div=True)
    if sys.version_info > (3, 0):
        assert isinstance(div, str)
        assert isinstance(script, str)
    if sys.version_info < (2, 8):
        assert isinstance(div, basestring)
        assert isinstance(script, basestring)
    assert '</div>' in div.split(), "Error, no </div> string in div variable"
    assert 'type="text/javascript">' in script.split(), "Invalid JS in script"
    assert 'Bokeh.$(function()' in script.split(), "Bokeh.func not in script"


def test_xyplot_autotile():
    """Check the auto-titles of plots are correct"""
    grobj = GraphKPIs()
    p = grobj.xy_scatter(x='stargazers', y='fork_count')
    assert p.title.text == 'Stargazers Vs. Fork Count'
    p2 = grobj.xy_scatter(x='num_contributors', y='total_commits')
    assert p2.title.text == 'Num Contributors Vs. Total Commits'


def test_error_if_no_db():
    """Check errors are correctly raised if a database file is missing."""
    if os.path.isfile('tinydb_for_KPI.json'):
        db_fname = 'tinydb_for_KPI.json'
        tmp_fname = 'tmp_rename_for_test'
        os.rename(src=db_fname, dst=tmp_fname)
        with raises(IOError):
            gobj = GraphKPIs()
        os.rename(src=tmp_fname, dst=db_fname)
    else:
        print("No tinydb file present: unable to test GraphKPIs error raising")
