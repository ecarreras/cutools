#!/usr/bin/env python
import sys
import tempfile
from plumbum.cmd import git, md5sum, rm

GIT_STATUS = {
    'M': 'Modified',
    '??': 'Untracked'
}

def get_md5_files():
    res = []
    files =  [x for x in git['status', '--porcelain']().split('\n') if x]
    for file_status in files:
        status, fl = file_status.split()
        md5 = git['show', '%s:%s' % (sys.argv[1], fl)] | md5sum
        res.append('%s  %s' % (md5().split(' ')[0], fl))
    return '\n'.join(res) + '\n'

def main():
    status_files = get_md5_files()
    tmpf = tempfile.mkstemp()[1]
    f = open(tmpf, 'w')
    f.write(status_files)
    f.close()
    res = md5sum['-c', tmpf](retcode=None)
    print res
    rm[tmpf]()
    

if __name__ == '__main__':
    main()