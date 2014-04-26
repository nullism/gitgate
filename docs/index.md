Title: Introduction

GitGate Overview
================

Flow Chart
----------

![Flow Chart](http://gitgate.nullism.com/uploads/gitgate-flow-basic.png)

Frequently Asked Questions
--------------------------

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

### How does GitGate handle merges? 

GitGate *copies* code from a development repository to a stable repository. 
Merge conflicts only arise when two commits that include the same file 
are waiting to be "merged" into the stable repo, and in that case GitGate
merges them in the proper order. Because developers use
the development repository, merge conflicts are handled prior to getting
into GitGate - removing the "code limbo" problems of tools like Gerrit.

Getting Started
===============

Initial Setup
-------------

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
    $ gitgate site create
    Path [/home/yolo/mysites] /home/yolo/mysites/GitGate
    Database path [/home/yolo/mysites/GitGate/global.db]
    ...
    Site created!

### Create a Project

    $ cd ~/mysites/GitGate
    $ gitgate project create
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

### Updating Changes

Let's say commit `cbea1644d86b03d63e98f67a97d102ae7825ab21` which contained
the files: `header.html`, `specialcode.js`, and `server.py` was **rejected**
because of broken code in `server.py`.

After fixing server.py in your development checkout, simply commit like so:

    $ git add server.py
    $ git commit -m "clone:cbea1644d86b03d63e98f67a97d102ae7825ab21"
    $ git push origin master

The `clone:<sha1>` command simply creates a brand new commit in GitGate
by cloning the older commit. The code reviewers will see a new commit in GitGate with 
the same message as the older commit (but hopefully when they test it will work).

This process is generally considered much easier than using `Change IDs`.

Merging
-------

Changes are merged into the stable repository when the following criteria is met:

* The commit has been *approved*
* The commit is older than any other pending change that includes the same files.
    * Pending changes are considered to be statuses of *committed*, *approved*, and *reviewed*.
    * This prevents older files being merged ontop of newer files.

GitGate changes merge in order.

### Merge Conflicts

Merge conflicts should not occur because they are handled at the time
the developer pushes to GitGate &mdash; it's just like using vanilla Git. 

However there is one scenario where things can get out of sync:

+ A developer pushes a commit
+ That commit is *rejected*
+ A different developer pushes a commit to the same file.
+ The second developer's commit is *approved* and *merged*.
+ The rejected change is *unrejected*, *approved*, and *merged*.
+ The files from the originally rejected change are now the latest in *stable*.



