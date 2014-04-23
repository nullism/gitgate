# GitGate Overview

![Flow Chart](http://gitgate.nullism.com/uploads/gitgate-flow-basic.png)

## What is GitGate? 

GitGate is a developer-friendly dual-repository code-review system for gatekeeping changes.

## How does GitGate work?

GitGate uses two repositories: *development* and *stable*. Developers commit to the *development* 
repository just like they normally would. Code from development is mirrored into *stable*
by checking out the commit in *development* and copying it to *stable*, and committing with `-C <commit sha1>` 
to duplicate the Author details. 

## What does repo access look like? 

    development/
        developer1 rw
        developer2 rw
        ...
        gitgate_user rw

    stable/
        gitgate_user rw
        build_user rw (ie: Jenkins)

# Getting Started

## Install GitGate

    $ sudo pip install gitgate

This will install GitGate and its requirements from PyPI. GitGate
requires Flask >= 0.9, and PeeWee > 2. 

## Setup Repositories

Assuming you have a current development repository called `swag` located
on GitHub:

    :::bash
    # Clone your existing repository
    $ git clone --bare https://github.com/yolo/swag.git tmp-swag.git
    $ cd tmp-swag.git
    # Create a new repository, called swag-stable
    $ git push --mirror https://github.com/yolo/swag-stable.git
    $ cd ../
    $ rm -rf tmp-swag.git
 

