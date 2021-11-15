# Working With Releases

More details about how to handle releases are available in the [release
runbook](https://lwd.atlassian.net/wiki/spaces/DD/pages/818184193/API+and+Portal+Runbook).

As a part of the release process it is useful to include some technical notes on
what the release includes. There is a make target to help automate some of this:

```sh
make release-notes
```

This will generate a list of the commits impacting an API release. For the
commits that follow the project convention for commit messages, the Jira ticket
will be linked. Everyone does not follow the convention nor will every commit
have a Jira ticket associated.

But this will provide a starting point. By default it will generate the list of
commits that are different between what is deployed to stage (indicated by the
`deploy/api/stage` branch) and what is on `main`. You can change the range of
commits it considers by passing in `refs`, for example only looking for changes
between release candidates:

```sh
make release-notes refs="api/v1.3.0-rc1..api/v1.3.0-rc2"
```

The work will generally fall into one of a number of categories, with changes to:
- ECS tasks for background jobs
- The API service itself
- CI tweaks

It's useful to group the release notes broadly by these buckets to clarify what
this particular release will impact.

It's also usually useful to group the tickets by team, which piping to `sort`
can help facilitate:

```sh
make release-notes | sort
```

Ultimately culminating in something like the notes for
[api/v1.3.0](https://github.com/EOLWD/pfml/releases/tag/api%2Fv1.3.0).

## Figuring out what's released where

There are a couple other make targets that could be useful. Note these all work
off of your local git repo, so can only be as accurate as your local checkout
is. You will generally want to run `git fetch origin` before these if you want
the most up-to-date info.

`where-ticket` will search the release branches for references to the provided
ticket number:

```sh
$ make where-ticket ticket=API-1000
## origin/main ##
e7fb31752 API-1000: Do not add "MA PFML - Limit" plan to FINEOS service agreements (#2272)

## origin/deploy/api/stage ##
e7fb31752 API-1000: Do not add "MA PFML - Limit" plan to FINEOS service agreements (#2272)

## origin/deploy/api/prod ##
e7fb31752 API-1000: Do not add "MA PFML - Limit" plan to FINEOS service agreements (#2272)

## origin/deploy/api/performance ##
e7fb31752 API-1000: Do not add "MA PFML - Limit" plan to FINEOS service agreements (#2272)

## origin/deploy/api/training ##

```

So in this example, API-1000 has been deployed to every environment but `training`.

`whats-released` lists some info about the latest commits on the release branches:

```sh
$ make whats-released
## origin/main ##
 * Closest tag: api/v1.3.0-rc2-48-g4465cfb72
 * Latest commit: 4465cfb72 (origin/main, main) END-338: Convert employer response and remove notification checking (#2386)

## origin/deploy/api/stage ##
 * Closest tag: api/v1.3.0
 * Latest commit: 6e86eab29 (tag: api/v1.3.0-rc3, tag: api/v1.3.0, origin/deploy/api/stage, origin/deploy/api/prod) EMPLOYER-685 Add logging reqs to LA FINEOS registration script (#2349)

## origin/deploy/api/prod ##
 * Closest tag: api/v1.3.0
 * Latest commit: 6e86eab29 (tag: api/v1.3.0-rc3, tag: api/v1.3.0, origin/deploy/api/stage, origin/deploy/api/prod) EMPLOYER-685 Add logging reqs to LA FINEOS registration script (#2349)

## origin/deploy/api/performance ##
 * Closest tag: api/v1.3.0-rc2
 * Latest commit: 13ba0f2c3 (tag: api/v1.3.0-rc2, origin/deploy/api/performance) remove ecr scan github action (#2333)

## origin/deploy/api/training ##
 * Closest tag: api/v1.1.0-rc1-48-ga6fb1f6bc
 * Latest commit: a6fb1f6bc (origin/deploy/api/training) API-999 Prod-Check Not Working as Expected (#2322)
```

So here can see `api/v1.3.0` is on both `stage` and `prod`, `performance` is on
`api/v1.3.0-rc2`, and something a little ahead of `api/v1.1.0-rc1` is on
`training`.