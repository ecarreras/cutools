#!/usr/bin/env python
import md5
import sys
from clint.textui import indent, puts, colored, progress
from plumbum.cmd import git


def get_chunks(diff):
    diff = clean_diff(diff)
    chunk = []
    chunks = []
    for line in diff.split('\n'):
        if not line:
            continue
        if line.startswith('@@ '):
            if chunk:
                chunks.append('\n'.join(chunk))
            chunk = [line]
        else:
            chunk.append(line)
    if chunk:
        chunks.append('\n'.join(chunk))
    return chunks


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


def clean_chunk(chunk):
    return '\n'.join([x[1:] for x in chunk.split('\n')
                      if x and x[0] not in ('-', '@')])


def print_diff(diff):
    for line in diff.split('\n'):
        line = unicode(line).encode('utf-8')
        if line.startswith('+'):
            puts(colored.green(line))
        elif line.startswith('-'):
            puts(colored.red(line))
        else:
            puts(line)


def get_md5_files():
    res = []
    files = ['%s' % x for x in git['ls-files', '-m']().split('\n') if x]
    for fl in files:
        pymd5 = md5.new(unicode(git['show', '%s:%s' % (sys.argv[1], fl)]()).encode('utf-8')).hexdigest()
        res.append('%s %s' % (pymd5, fl))
    return '\n'.join(res) + '\n'

def main():
    status_files = get_md5_files()
    count = 0
    failed_files = []
    local_rev = git['rev-parse', 'HEAD']().strip()
    remote_rev = git['rev-parse', sys.argv[1]]().strip()
    for line in status_files.split('\n'):
        if not line:
            break
        pymd5, check_file = line.split(' ')
        if md5.new(open(check_file, 'r').read()).hexdigest() != pymd5:
            hcommand = git['log', '--no-merges', '--pretty=oneline',
                           '%s..%s' % (local_rev, remote_rev),
                           check_file]
            local_chunks = {}
            for lchunk in get_chunks(git['diff', check_file]()):
                local_chunks[md5.new(unicode(lchunk).encode('utf-8')).hexdigest()] = lchunk
            hlines = [x for x in hcommand().split('\n') if x]
            puts("File: %s modified remotely. Searching for local modifications in remote by %s commits" % (check_file, len(hlines)))
            puts("Local chunks: %s" % ', '.join(local_chunks.keys()))
            for hline in hlines:
                if not hline:
                    continue
                commit = hline.split(' ')[0]
                with indent(4):
                    puts(colored.yellow("**** DIFF %s^1..%s ****"
                                        % (commit, commit)))
                remote_chunks = [md5.new(unicode(x).encode('utf-8')).hexdigest()
                                 for x in get_chunks(git['diff', '%s^1..%s'% (commit, commit),
                                      check_file]())]
                with indent(4):
                    puts("Remote chunks: %s" % ', '.join(remote_chunks))
                for lchunk in local_chunks.keys():
                    if lchunk in remote_chunks:
                        with indent(4):
                            puts(colored.green("Local chunk %s found in remotes!" % lchunk))
                        del local_chunks[lchunk]
                    else:
                        # Secound round
                        rfile = git['show', '%s:%s' % (sys.argv[1], check_file)]()
                        chunk = clean_chunk(local_chunks[lchunk])
                        if rfile.find(chunk) >= 0:
                            with indent(4):
                                puts(colored.green("Local chunk %s found in remotes!" % lchunk))
                            del local_chunks[lchunk]
            if local_chunks:
            	count += 1
                for chunk in local_chunks.values():
                    print_diff(chunk)
                puts(colored.red("[x] %s %s" % (pymd5, check_file)))
            else:
                puts(colored.green("[o] %s %s" % (pymd5, check_file)))
        else:
            puts(colored.green(line))
    if count:
        puts(colored.red("*** WARNING: %s files doesn't match" % count))

if __name__ == '__main__':
    main()
