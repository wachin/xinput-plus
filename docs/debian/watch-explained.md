# Understanding `debian/watch` and `uscan`

## What they do

`debian/watch` tells `uscan` where to find new upstream versions. `uscan` reads
the current version from `debian/changelog`, scans the configured release page,
extracts version numbers from matching links, downloads the newest tarball, and
renames it to the format expected by Debian.

The current watch file uses GitHub tags:

```watch
version=4
opts=filenamemangle=s%.*archive/refs/tags/v?(\d[\d\.]*)\.tar\.gz%xinput-plus-$1.tar.gz% \
  https://github.com/wachin/xinput-plus/tags .*/archive/refs/tags/v?(\d[\d\.]*)\.tar\.gz
```

`version=4` selects the modern watch-file format. The second line contains the
index URL and the regular expression used to find download links. In the
expression, `v?` accepts tags both with and without a leading `v`, while
`(\d[\d\.]*)` captures a numeric dotted version such as `6.6.2`.

`filenamemangle` converts a GitHub filename such as `v6.6.2.tar.gz` to
`xinput-plus-6.6.2.tar.gz`. This gives `dpkg-source` the conventional upstream
filename it expects.

GitHub may expose the same link more than once in verbose `uscan` output. This
is harmless. Both `v6.6.2` and `6.6.2` tags match the current expression.

## OpenPGP signatures

GitHub-generated archives under `/archive/refs/tags/` do not include detached
signatures. Consequently, this setup cannot verify an OpenPGP signature and
Lintian may report `debian-watch-does-not-check-openpgp-signature` as an
informational issue.

For signature verification, upload a release tarball and its `.asc` signature
as GitHub Release assets, then use a watch file like this:

```watch
version=4
opts=\
  uversionmangle=s/^v//,\
  filenamemangle=s%.*/download/v?(\d[\d\.]*)/xinput-plus-\1\.tar\.xz%xinput-plus-$1.tar.xz%,\
  pgpsigurlmangle=s/$/.asc/
https://github.com/wachin/xinput-plus/releases .*/download/v?(\d[\d\.]*)/xinput-plus-\1\.tar\.xz
```

Here, `uversionmangle` removes the optional leading `v`, `filenamemangle`
creates the Debian-style filename, and `pgpsigurlmangle` tells `uscan` to fetch
the signature from the tarball URL with `.asc` appended. This requires publishing
both assets for every release.

## Prerelease versions

The current capture group accepts only digits and dots. To support suffixes such
as `-rc1`, extend the expression and convert the suffix to Debian's `~rc1`
ordering when necessary:

```watch
version=4
opts=\
  uversionmangle=s/-rc/~rc/;\
  filenamemangle=s%.*archive/refs/tags/v?(\d[\d\.~-]*)\.tar\.gz%xinput-plus-$1.tar.gz%
https://github.com/wachin/xinput-plus/tags .*/archive/refs/tags/v?(\d[\d\.~-]*)\.tar\.gz
```

`uversionmangle` transforms the upstream version found by `uscan`.
`dversionmangle` can similarly transform the Debian version before comparison.

## Repacked tarballs

If a future source release must exclude files such as precompiled blobs, list
them with `Files-Excluded` in `debian/copyright` and add
`repacksuffix=+ds` to the watch options. `uscan` will then repack the archive and
append `+ds` to the upstream version. This is not currently needed by this
project.

Lintian may also recommend that `uscan` create a symlink for the `.orig.tar.*`
rather than copying it. A `Successfully symlinked` message confirms that this is
already happening.

## Test the watch file

Run:

```bash
uscan --verbose --force-download
```

Check that the output reports the newest version, downloads the expected
archive, renames it to `xinput-plus-<version>.tar.gz`, and creates or links the
corresponding `.orig.tar.gz` file.

As release practices evolve, keep tag names stable and ensure that the upstream
version in `debian/changelog` matches the published release version.
