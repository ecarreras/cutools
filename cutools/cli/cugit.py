from hashlib import md5
from subcmd.app import App
from subcmd.decorators import arg, option
from cutools.vcs.git import Git
from cutools.diff import get_hashed_chunks, clean_chunk, print_diff
from cutools import VERSION
from clint.textui import puts, colored

RED = colored.red
GREEN = colored.green

class CuGitApp(App):
    name = "cugit"
    version = VERSION

    def check_files(self, git):
        res = {}
        git.fetch()
        for pymd5, check_file in git.get_md5_files():
            res[check_file] = {'checksum': pymd5, 'local_chunks': {}}
            if md5(open(check_file, 'r').read()).hexdigest() != pymd5:
                local_chunks = get_hashed_chunks(git.get_chunks(check_file))
                rev_from = git.local_rev
                rev_to = git.remote_rev
                for commit in git.get_commits(check_file, rev_from, rev_to):
                    remote_chunks = [
                        md5(unicode(x).encode('utf-8')).hexdigest()
                        for x in git.get_chunks(check_file, commit)
                    ]
                    for lchunk in local_chunks.keys():
                        if lchunk in remote_chunks:
                            del local_chunks[lchunk]
                        else:
                            rfile = git.get_remote_file(check_file)
                            chunk = clean_chunk(local_chunks[lchunk])
                            if rfile.find(chunk) >= 0:
                                del local_chunks[lchunk]
                res[check_file]['local_chunks'] = local_chunks
        return res

    @arg('upstream', help='Upstream branch')
    @option('--diff', action='store_true', default=False,
            help="Show the diff (default: %(default)s)")
    def do_check(self, options):
        """Checks local modifcations if are in upstream.
        """
        git = Git(options.upstream)
        n_files = 0
        n_chunks = 0
        status = self.check_files(git)
        for check_file in status:
            pymd5 = status[check_file]['checksum']
            local_chunks = status[check_file]['local_chunks']
            if local_chunks:
                n_files += 1
                n_chunks += len(local_chunks.values())
                puts(RED("FAIL %s %s" % (pymd5, check_file)))
                if options.diff:
                    for chunk in local_chunks.values():
                        print_diff(chunk)
            else:
                puts(GREEN("OK %s %s" % (pymd5, check_file)))

    @arg('upstream', help='Upstream branch')
    def do_diff(self, options):
        """Print the diff to apply after the upgrade.
        """
        git = Git(options.upstream)
        status = self.check_files(git)
        for check_file in status:
            local_chunks = status[check_file]['local_chunks']
            if local_chunks:
                print_diff(git.get_diff(check_file))

    @arg('upstream', help='Upstream branch')
    @option('--interactive', action='store_true', default=False,
            help="Interactive mode (default: %(default)s)")
    def do_upgrade(self, options):
        git = Git(options.upstream)
        puts("Making a savepoint... ", newline=False)
        savepoint = git.savepoint()
        puts("Savepoint id: %s" % savepoint)
        try:
            diff_files = self.do_diff(options)
            diff_to_apply = []
            for check_file, diff in diff_files:
                header = header_diff(diff)
                for chunk in get_chunks(diff):
                    diff_to_apply.append(header + chunk)
            if git.local_rev == git.remote_rev:
                puts("Already up-to-date.")
            else:
                puts("Merging %s %s..%s " %
                     (options.upstream, git.local_rev[:7], git.remote_rev[:7]),
                     newline=False)
                git.merge()
                puts("Done!")
            if not diff_to_apply:
                puts("Nothing to apply.")
                sys.exit(0)
            puts("Applying patches...")
            for to_apply in diff_to_apply:
                print_diff(to_apply)
                if options.interactive:
                    apply = yn('Apply?')
                    if not apply:
                        patch_file = write_tmp_patch(to_apply)
                        puts(colored.yellow("Skipped patch. Saved to %s"
                                            % patch_file))
                        continue
                git.apply_diff(to_apply)
        except (KeyboardInterrupt, Exception) as e:
            puts(colored.red(str(e)))
            # If anything goes wrong rollback to rescue!
            puts("Restoring savepoint %s " % savepoint, newline=False)
            git.restore(savepoint.identity)
            puts("Done!")


app = CuGitApp()
