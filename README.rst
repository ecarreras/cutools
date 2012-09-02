Cutools (a.k.a Check Upgrade Tools)
===================================

For this moment only **git** is supported.

Checks if local modifications are in remote branch
--------------------------------------------------

```bash
$ cugit check origin/master
```

Now showing the *diff*

```bash
$ cugit check origin/master --diff
```

Generate a diff for applying after merge remote branch
------------------------------------------------------

```bash
$ cugit diff origin/master
```

Saving the diff

```bash
$ cugit diff origin/master > to_apply.diff
```

