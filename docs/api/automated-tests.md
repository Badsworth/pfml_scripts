# Automated Tests

For writing tests see [/docs/api/writing-tests.md](/docs/api/writing-tests.md).

There are various `test*` make targets set up for convenience.

To run the entire test suite:

```sh
make test
```

Ultimately the targets just wrap the test runner
[pytest](https://docs.pytest.org) with minor tweaks and wrapping it in helper
tools. To pass arguments to `pytest` through `make test` you can set the `args`
variable.  For example, to run only the tests in `test_user.py`:

```sh
make test args=tests/api/test_users.py
```

To run only a single test:

```sh
make test args=tests/api/test_users.py::test_users_get
```

To pass multiple arguments:

```sh
make test args="-x tests/api/test_users.py"
```

For a more complete description of the many ways you can select tests to run and
different flags, [refer to the pytest
docs](https://docs.pytest.org/en/latest/usage.html) (and/or `pytest --help`).

## During Development

While working on a part of the system, you may not be interested in running the
entire test suite all the time. To just run the test impacted by the changes
made since they last ran, you can use:

```sh
make test-changed
```

Note that it will run the entire test suite the first time that command is run
to collect which source files touch which tests, subsequent runs should only run
the tests that need to run.

And instead of running that command manually, you can kick off a process to
automatically run the tests when files change with:

```sh
make test-watch-changed
```

To run tests decorated with `@pytest.mark.dev_focus` whenever a file is saved:

```sh
make test-watch-focus
```

`test-watch-focus` is a wrapper around the more flexible `test-watch` Makefile target
that we can use to re-run specific tests whenever a file changes, for instance.

```sh
make test-watch args=tests/api/test_users.py::test_users_get
```

Arguments for `test-watch` are the same as args for `make test` as discussed in the section above.

To run only unit tests:

``` sh
make test-unit
```