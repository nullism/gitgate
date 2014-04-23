# GitGate Overview

## Flow Chart

![Flow Chart](http://gitgate.nullism.com/uploads/gitgate-flow-basic.png)

## Frequently Asked Questions

### What is GitGate? 

GitGate is a developer-friendly dual-repository code-review system for gatekeeping changes.

### How does GitGate work?

GitGate uses two repositories: *development* and *stable*. Developers commit to the *development* 
repository just like they normally would. Code from development is mirrored into *stable*
by checking out the commit in *development* and copying it to *stable*, and committing with `-C <commit sha1>` 
to duplicate the Author details. 

### What does repo access look like? 

    development/
        developer1 rw
        developer2 rw
        ...
        gitgate_user rw

    stable/
        gitgate_user rw
        build_user rw (ie: Jenkins)

# Getting Started

## Initial Setup

### Install GitGate from PyPI

    $ sudo pip install gitgate

This will install GitGate and its requirements from PyPI. GitGate
requires Flask >= 0.9, and PeeWee > 2. 

### Setup Repositories

Assuming you have a current development repository called `swag` located
on GitHub:

    # Clone your existing repository
    $ git clone --bare https://github.com/yolo/swag.git tmp-swag.git
    $ cd tmp-swag.git
    # Create a new repository, called swag-stable
    $ git push --mirror https://github.com/yolo/swag-stable.git
    $ cd ../
    $ rm -rf tmp-swag.git
 
### Create a Site

    $ cd ~/mysites
    $ gitgate create-site
    Path [/home/yolo/mysites] /home/yolo/mysites/GitGate
    Database path [/home/yolo/mysites/GitGate/global.db]
    ...
    Site created!

### Create a Project

    $ cd ~/mysites/GitGate
    $ gitgate create-project
    Project name: swag
    Project path [/home/yolo/mysites/GitGate/projects/swag]
    Development clone url: https://github.com/yolo/swag.git
    Stable clone url: https://github.com/yolo/swag-stable.git
    ... 
    Project created!

### Start the Daemon

    $ cd ~/mysites/GitGate
    $ ./daemon.py &

### Start the Test Server

    $ cd ~/mysites/GitGate
    $ ./testserver.py
    Serving on localhost:5000
    ...

### Clone the Development Repository

This is the repository your developers work against.

    $ cd ~/github
    $ git clone https://github.com/yolo/swag.git

## Committing

### Making Changes

Using the example from Initial Setup.

    $ cd ~/github/swag
    $ echo "Here's a new file" > newfile.txt
    $ git commit newfile.txt -m "Added a new file"
    $ git push origin master

### Reviewing and Approving Changes

Navigate to `yourhost:5000` and login using the admin credentials
created in the Project Creation step.


