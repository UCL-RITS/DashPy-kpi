from DashPykpi.kpistats import KpiStats
import os


def test_public_repo_access():
    url = "https://github.com/benlaken/Comment_BadruddinAslam2014"  # 21commits
    test = KpiStats(url)
    test.work()
    assert test.stats['total_commits'] > 20


def test_private_repo_access():
    url = "https://github.com/UCL-RITS/RSD-Dashboard"  # >1k commits + PRIVATE
    test = KpiStats(url)
    test.work()
    assert test.stats['total_commits'] > 1000
