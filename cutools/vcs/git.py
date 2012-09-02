from os import remove
from hashlib import md5, sha1
from cutools.vcs import VCSInterface
from cutools.diff import get_chunks, write_tmp_patch
from plumbum.cmd import git


class SavePoint(object):
    def __init__(self, rev, diff):
        self.identity = sha1('%s_%s' % (rev, diff)).hexdigest()[:7]
        self.rev = rev
        self.diff = diff

    def __str__(self, *args, **kwargs):
        return self.identity

    def __repr__(self, *args, **kwargs):
        return '<SavePoint %s>' % self.identity


class Git(VCSInterface):
    """Git implementation for Check Upgrade Tools.
    """
    def __init__(self, upstream):
        self.upstream = upstream
        self.savepoints = {}

    def savepoint(self):
        sp = SavePoint(self.local_rev, self.get_diff())
        self.savepoints[sp.identity] = sp
        return sp

    def restore(self, savepoint_id, remove=True):
        if savepoint_id not in self.savepoints:
            raise Exception("This savepoint doesn't exists in this repo.")
        sp = self.savepoints[savepoint_id]
        git['reset', '--hard', sp.rev]()
        self.apply_diff(sp.diff)
        if remove:
            del self.savepoints[savepoint_id]

    def get_md5_files(self):
        res = []
        files = ['%s' % x for x in git['ls-files', '-m']().split('\n') if x]
        for fl in files:
            cmd = git['show', '%s:%s' % (self.upstream, fl)]
            pymd5 = md5(unicode(cmd()).encode('utf-8')).hexdigest()
            res += [(pymd5, fl)]
        return res

    @property
    def local_rev(self):
        return git['rev-parse', 'HEAD']().strip()

    @property
    def remote_rev(self):
        return git['rev-parse', self.upstream]().strip()

    def get_commits(self, check_file, rev_from, rev_to):
        hcommand = git['log', '--no-merges', '--pretty=oneline',
                           '%s..%s' % (rev_from, rev_to),
                           check_file]
        return [x.split(' ')[0] for x in hcommand().split('\n') if x]

    def get_chunks(self, check_file, commit=None):
        return get_chunks(self.get_diff(check_file, commit))

    def get_diff(self, check_file, commit=None):
        if commit:
            cmd = git['diff', '%s^1..%s'% (commit, commit), check_file]
        else:
            cmd = git['diff', check_file]
        return cmd()

    def get_remote_file(self, check_file):
        return git['show', '%s:%s' % (self.upstream, check_file)]()