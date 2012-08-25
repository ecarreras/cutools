from hashlib import md5
from cutools.vcs import VCSInterface
from cutools.diff import get_chunks
from plumbum.cmd import git
from plumbum.commands import ProcessExecutionError

class Git(VCSInterface):
    """Git implementation for Check Upgrade Tools.
    """
    def __init__(self, upstream):
        self.upstream = upstream

    def autodetect(self):
        try:
            git['branch']()
            return True
        except ProcessExecutionError:
            return False

    def get_md5_files(self):
        res = []
        files = ['%s' % x for x in git['ls-files', '-m']().split('\n') if x]
        for fl in files:
            cmd = git['show', '%s:%s' % (self.upstream, fl)]
            pymd5 = md5(unicode(cmd()).encode('utf-8')).hexdigest()
            res.append('%s %s' % (pymd5, fl))
        return res

    @property
    def local_rev(self):
        return git['rev-parse', 'HEAD']().strip()

    @property
    def remote_rev(self):
        return git['rev-parse', self.upstrem]().strip()

    def get_commits(self, check_file, rev_from, rev_to):
        hcommand = git['log', '--no-merges', '--pretty=oneline',
                           '%s..%s' % (rev_from, rev_to),
                           check_file]
        return [x.split(' ')[0] for x in hcommand().split('\n') if x]

    def get_chunks(self, commit, check_file):
        return get_chunks(
            git['diff', '%s^1..%s'% (commit, commit), check_file]()
        )

    def get_remote_file(self, check_file):
        return git['show', '%s:%s' % (self.upstream, check_file)]()