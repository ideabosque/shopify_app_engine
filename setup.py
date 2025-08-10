#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "jeffreyw"

from setuptools import find_packages, setup

setup(
    name="Shopify-App-Engine",
    version="0.0.1",
    author="Abacus IP LLC",
    author_email="devops@abacusipllc.com",
    description="Shopify App Engine",
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms="Linux",
    install_requires=[
        "SilvaEngine-Utility",
        "graphene",
        "boto3",
    ],
    classifiers=[
        "Programming Language :: Python",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
