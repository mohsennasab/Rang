# Releasing Rang

Pushing a version tag publishes the Python package to PyPI. There is no API
token stored anywhere. PyPI trusts this repository directly, and GitHub gives
the publish job a short lived identity token for each run.

## One time setup on PyPI

This only has to be done once per project.

1. Sign in to PyPI and open
   https://pypi.org/manage/project/rang/settings/publishing/
2. Under "Add a new publisher", choose GitHub and fill in:

   | field | value |
   | --- | --- |
   | Owner | `mohsennasab` |
   | Repository name | `Rang` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

3. Save.

The environment name has to match the `environment:` block in
[.github/workflows/publish.yml](.github/workflows/publish.yml). GitHub creates
the environment the first time the workflow runs, so there is nothing to set
up on that side.

Once this is in place, any API tokens can be deleted from
https://pypi.org/manage/account/token/ and from `~/.pypirc`. Nothing needs
them any more.

## Cutting a release

The version lives in three files and the test suite fails if they disagree.

1. `python/rang/__init__.py`, the `__version__` line
2. `r/DESCRIPTION`, the `Version:` line
3. `CITATION.cff`, the `version:` and `date-released:` lines

Update all three, then:

```
python -m pytest tests/ -q
git add -A
git commit -m "Release 0.3.0"
git push
```

Merge to `main` through a pull request as usual, then tag the merge commit:

```
git checkout main
git pull
git tag -a v0.3.0 -m "Rang 0.3.0"
git push origin v0.3.0
```

Pushing the tag is what triggers the release. Watch it under the Actions tab.

## What the workflow does

The build job checks that the tag matches `rang.__version__`, runs the test
suite, builds the wheel and sdist, validates them the way PyPI will, and
installs the wheel into a clean environment to confirm it imports on its own.

Only then does the publish job run, and it holds nothing except permission to
request an identity token. If any check fails, nothing is published.

A version number on PyPI can never be reused, so the tag check exists to stop
a mistyped tag from burning one.

## Running it without publishing

Use "Run workflow" on the Actions tab to build and check the current state of
`main`. The publish job is skipped unless the run came from a tag, so this is
a safe rehearsal.

## The R package

The R package is not on CRAN. CRAN already lists an unrelated package called
`rang`, which is why this one is `Rang`, and CRAN treats the two names as
conflicting. People install it from GitHub with
`remotes::install_github("mohsennasab/Rang", subdir = "r")`, which always
tracks `main`, so an R change is released as soon as it merges.
