from DashPykpi.kpistats import KpiStats


def test_private_repo_access():
    url = "https://github.com/UCL-RITS/RSD-Dashboard"# >1k commits + PRIVATE
    test = KpiStats(url)
    test.work()
    assert test.stats['total_commits'] > 1000
