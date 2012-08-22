#!/usr/bin/env python
import sys
import tempfile
from clint.textui import puts, colored, progress
from plumbum.cmd import git, md5sum, rm

def clean_diff(text):
    res = []
    skip = True
    for line in text.split('\n'):
        if line.startswith('diff --git'):
            skip = True
        if line.startswith('@@ '):
            skip = False
        if not skip:
            res.append(line)
     return '\n'.join(res)


def get_md5_files():
    res = []
    if git['--version']().split(' ')[2] < '1.7.0.0':
        files = [' M %s' % x for x in git['ls-files', '-m']().split('\n') if x]
    else:
        files =  [x for x in git['status', '--porcelain']().split('\n') if x]
    for file_status in files:
        fl = file_status.split()[1]
        md5 = git['show', '%s:%s' % (sys.argv[1], fl)] | md5sum
        res.append('%s  %s' % (md5().split(' ')[0], fl))
    return '\n'.join(res) + '\n'

def main():
    status_files = get_md5_files()
    tmpf = tempfile.mkstemp()[1]