#!/usr/bin/env python3
"""
Setup script for MLS PDF Data Extractor
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements():
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt'), encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="ipDealMachine",
    version="1.0.5",
    author="ipDealMachine Team",
    author_email="",
    description="A desktop application for extracting real estate data from MLS PDF documents and performing financial projections",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ipDealMachine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'ipdealmachine=Main:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.txt', '*.md'],
    },
    keywords="real-estate mls pdf extraction financial-analysis investment",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ipDealMachine/issues",
        "Source": "https://github.com/yourusername/ipDealMachine",
    },
)