#!/usr/bin/env python
import sys
import tempfile
from clint.textui import puts, colored, progress
from plumbum.cmd import git, md5sum, rm

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
    f = open(tmpf, 'w')
    f.write(status_files)
    f.close()
    count = 0
    failed_files = []
    local_rev = git['rev-parse', 'HEAD']()
    remote_rev = git['rev-parse', sys.argv[1]]()
    for line in md5sum['-c', tmpf](retcode=None).split('\n'):
        if line.endswith('FAILED'):
            failed_files.append(line.rstrip(': FAILED')
            hcommand = (git['log', '--no-merges', '--prety=oneline',
                             '%s..%s' % (local_rev, remote_rev)]
            for hline in progress.mill(hcommand().split('\n')):
                print hline
            count += 1
        else:
            puts(colored.green(line))
    rm[tmpf]()
    if count:
        puts(colored.red("*** WARNING: %s files doesn't match" % count))

if __name__ == '__main__':
    main()
