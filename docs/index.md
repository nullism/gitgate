# GitGate Overview

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
