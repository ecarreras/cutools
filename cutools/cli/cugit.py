from hashlib import md5
from subcmd.app import App
from subcmd.decorators import arg
from cutools.vcs.git import Git
from cutools import VERSION
from clint.textui import puts, colored

class CuGitApp(App):
    name = "cugit"
    version = VERSION

    @arg('upstream')
    def do_check(self, options):
        """Checks local modifcations if are in upstream.
        """
        git = Git(options.upstream)
        for pymd5, check_file in git.get_md5_files():
            if md5(open(check_file, 'r').read()).hexdigest() != pymd5:
                local_chunks = {}
                rev_from = git.local_rev
                rev_to = git.remote_rev
                for lchunk in git.get_chunks(check_file):
                    commits = git.get_commits(check_file, rev_from, rev_to)
                    for commit in commits:
                        puts("File: %s modified remotely by %s commits."
                             "Searching for local modifications in remote"
                             % (check_file, len(commits)))
            else:
                puts(colored.green("[o] %s %s" % (pymd5, check_file)))

app = CuGitApp()