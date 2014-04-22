#!/usr/bin/env python
import models as dbm
import time
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

on_commit = None
on_merge = None

running = False

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

