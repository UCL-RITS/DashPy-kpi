from DashPykpi.kpistats import KpiStats, GitURLs
import os


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
