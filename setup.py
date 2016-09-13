from setuptools import setup, find_packages

setup(
    name="DashPykpi",
    version="0.1.1",
    description='Functions to create KPI info for RSD Dashboard from Github',
    url='https://github.com/UCL-RITS/DashPy-kpi',
    author='Benjamin A. Laken',
    author_email='b.laken@ucl.ac.uk',
    license='MIT',
    packages=find_packages(exclude=['*test']),
    install_requires=['pandas'],
    keywords=['RSD', 'Dashboard', 'kpi', 'Github']
)
