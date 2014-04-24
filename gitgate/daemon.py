#!/usr/bin/env python
import models as dbm
import time
import logging
import sys
import re
import datetime

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

on_commit = None
on_merge = None
running = False



def clone_commit(new_sha1, old_sha1, file_changes, details):

    """ Clones a commit and its files """

    try:
        old_commit = dbm.Commit.get(sha1=old_sha1)
    except:
        return False

    new_date = details.get('author_date', datetime.datetime.now)

    commit = old_commit.clone(new_sha1=new_sha1, 
        new_author_date=new_date, clone_files=True)
    
    file_paths = [f[1] for f in file_changes]

    for old_cf in commit.files:
        if old_cf.file_path in file_paths:        
            old_cf.delete_instance()

    for status, fpath in file_changes:
        dbm.CommitFile.create(
            commit=commit,
            change_type=status,
            file_path=fpath)

    return commit

def check_for_commits(project):
    sha1s = project.git_control.get_sha1_diffs()
    handled_sha1s = [c.sha1 for c in project.commits]

    for sha1 in sha1s:
        logger.info("Found commit: %s"%(sha1))
        if sha1 in handled_sha1s:
            logger.info('Already handled')
            continue

        file_changes = project.git_control.get_commit_file_changes(sha1)

        if not file_changes:
            logger.info('No file changes')
            continue

        details = project.git_control.get_commit_details(sha1)
        message = details['message']
        commit = None

        ### Check for special handling

        # Check for "clone" 
        inc_match = re.search(r'clone:([a-zA-Z0-9]{20,45})', message)
        if inc_match:
            old_sha1 = inc_match.group(1)
            commit = clone_commit(old_sha1=old_sha1, new_sha1=sha1,
                file_changes=file_changes, details=details)
        
        
        # Create the commit and its files
        if not commit:    
            commit = dbm.Commit.create(sha1=sha1, project=project, branch='master',
                author_date=details['author_date'], author_name=details['author_name'],
                author_email=details['author_email'], status='committed',
                message=details['message'])
        
            for change in file_changes:
                cf = dbm.CommitFile.create(file_path=change[1], change_type=change[0], commit=commit)

        if on_commit:
            on_commit(commit)
    
        logger.info('Done')

def handle_approved(project):
    commits = (
        dbm.Commit.select()
        .where((dbm.Commit.status == 'approved') & (dbm.Commit.project == project))
        .order_by(dbm.Commit.author_date.asc()))
    
    for commit in commits:
        logger.info('Working on commit: %s'%(commit.sha1))
        if not commit.can_merge:
            logger.info("Can't merge")
            continue
        try:
            project.git_control.merge_commit(commit.sha1, branch=commit.branch)    
            commit.status = 'merged'
        except Exception as err:
            logger.exception(err)
            logger.warning('Could not merge commit due to above exception')
            commit.status = 'outdated'
        commit.save()

def start():
    running = True
    while running:
        projects = dbm.Project.select()
        for project in projects:
            project.git_control.update_all()
            check_for_commits(project)
            handle_approved(project)
        time.sleep(10)

def stop():
    running = False

if __name__ == "__main__":
    start()

