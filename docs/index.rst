.. GitGate documentation master file, created by
   sphinx-quickstart on Sat Apr 26 03:46:24 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to GitGate's documentation!
===================================

Contents:

.. toctree::
   :maxdepth: 2

    installation

Installation
============

::

    sudo pip install gitgate

GitGate requires Flask, Python SQLite3, Peewee ORM, and ArgParse. 
These dependencies should automatically be resolved via PyPI. 

Setup
=====

Getting started
---------------

Setting up the repositories
~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    git clone --bare https://github.com/yolo/swag.git tmp-swag.git
    cd tmp-swag.git
    git push --mirror https://github.com/yolo/swag-stable.git
    cd ../
    rm -rf tmp-swag.git
