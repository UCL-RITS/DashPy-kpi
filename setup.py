from setuptools import setup, find_packages

setup(
    name = "DashPy-kpi",
    version = "0.1",
    description='Functions to create KPI info for RSD Dashboard from Github',
    url='http://github.com/storborg/funniest',
    author='Benjamin A. Laken',
    author_email='b.laken@ucl.ac.uk',
    license='MIT',
    packages = find_packages(exclude=['*test']),
    install_requires = ['argparse'],
)
