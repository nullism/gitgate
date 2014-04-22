#!/usr/bin/env python
import subprocess
import os
import json
import shutil 
import dateutil.parser
import re

def git_command(cmd, cwd=None, args=[]):

    if not cwd:
        cwd = os.getcwd()
    cmds = ['/usr/bin/git',cmd] + args
    p = subprocess.Popen(cmds, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        cwd=cwd)
    stdout, stderr = p.communicate()
    status = p.returncode
    if status != 0:
        raise Exception('Error executing "git %s %s", error: %s'%(cmd, ' '.join(cmds), stderr))
    return stdout

class GitProject(object):   

    config = None

    def __init__(self, config):
        self.config = config


    @property
    def devel_path(self):
        return os.path.join(self.config.path, 'devel')
    
    @property
    def stable_path(self):
        return os.path.join(self.config.path, 'stable')

    def update_all(self):
        git_command('pull', cwd=self.devel_path, args=['origin','master'])
        git_command('pull', cwd=self.stable_path, args=['origin','master'])

    def create_devel_checkout(self):
        if os.path.exists(self.devel_path):
            # Remove dpath
            pass
        output = git_command('clone', cwd=self.config.path,
            args=[self.config.devel_clone_url, 'devel'])
        return True

    def create_stable_checkout(self):
        if os.path.exists(self.stable_path):
            pass
        output = git_command('clone', cwd=self.config.path,
            args=[self.config.stable_clone_url, 'stable'])
        git_command('remote', cwd=self.stable_path,
            args=['add', '-f', 'devel', self.config.devel_clone_url])
        return True

    def merge_commit(self, sha1, branch='master'):

        """ Merges commits via manual copying """

        git_command('checkout', cwd=self.devel_path, args=[sha1])
        git_command('checkout', cwd=self.stable_path, args=[branch])
        flist = self.get_commit_file_changes(sha1, branch=branch)
        for fc in flist:
            t, fname = fc
            devel_path = os.path.join(self.devel_path, fname)
            stable_path = os.path.join(self.stable_path, fname)

            if t == 'D':
                git_command('rm', cwd=self.stable_path, 
                    args=[fname])
            elif t in ['A', 'M']:
                shutil.copy2(devel_path, stable_path)
                git_command('add', cwd=self.stable_path,
                    args=[fname])                
            else:
                raise Exception('Unknown merge type: %s'%(t))
        
        git_command('commit', cwd=self.stable_path,
            args=['-C',sha1])
        git_command('push', cwd=self.stable_path,
            args=['origin', branch])
        git_command('checkout', cwd=self.devel_path, args=['master'])
        self.config.last_merge_sha1 = sha1
        self.config.save()
        return True

    def get_commit_details(self, sha1):
        output = git_command('show', cwd=self.devel_path,
            args=['--format=%H|xsplit|%an|xsplit|%ae|xsplit|%ai|xsplit|%B|xsplit|', 
            sha1])
        parts = output.split('|xsplit|')
        data = { 
            'author_name':parts[1],
            'author_email':parts[2],
            'author_date':dateutil.parser.parse(parts[3]),
            'message':parts[4]
        }
        return data

    def get_sha1_diffs(self, branch='master'):

        """ Returns a list of commit hashes not in stable """

        git_command('fetch', cwd=self.stable_path, args=['--all'])

        output = git_command('cherry', cwd=self.stable_path,
            args=[branch, 'remotes/devel/%s'%(branch)])
        shas = output.split('\n')
        diffs = [sha.split(' ')[-1] for sha in shas if '+' in sha]
        return diffs

    def get_file_diff(self, sha1, fpath, branch='master'):

        """ Returns a git diff -U10000 of a commit and file """

        git_command('checkout', cwd=self.devel_path, args=[branch])
        output = git_command('diff', cwd=self.devel_path,
            args=['--no-prefix', '-U10000', sha1+'^', sha1, fpath])
        output = re.split(r'@@.*?@@', output, 1)[-1]
        return output

    def get_commit_file_changes(self, sha1, branch="master"):

        """ Returns a list of STATUS, FILENAME changes """
    
        output = git_command('show', cwd=self.stable_path,
            args=['--name-status', '--format=%mSTART>>>', sha1])
        #print "OUTPUT: ===\n%s\n==="%(output)
        status_names = output.split('START>>>')[-1].split('\n')
        #print "STATUS NAMES = '''\n%s\n'''"%(status_names)
        stat_list = []
        for sname in status_names:
            #print "SNAME: ", sname
            if len(sname.strip()) < 1:
                continue
            status, name = sname.split('\t', 1)
            stat_list.append([status, name])
        return stat_list

