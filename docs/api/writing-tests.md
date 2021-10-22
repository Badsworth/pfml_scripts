# Writing Tests

[pytest](https://docs.pytest.org) is our test runner, which is simple but
powerful. If you are new to pytest, reading up on how [fixtures
work](https://docs.pytest.org/en/latest/explanation/fixtures.html) in particular might be
helpful as it's one area that is a bit different than is common with other
runners (and languages).

## Naming

pytest automatically discovers tests by [following a number of
conventions](https://docs.pytest.org/en/stable/goodpractices.html#conventions-for-python-test-discovery)
(what it calls "collection").

For this project specifically:

- All tests live under `tests/`
- Under `tests/`, the organization mirrors the source code structure, but
  without the `massgov/pfml/` part, so for example:
  - The tests for `massgov/pfml/api/` live under `tests/api/`
  - `massgov/pfml/util/aws/` under `test/util/aws/`.
- Create `__init__.py` files for each directory. This helps [avoid name
  conflicts when pytest is resolving
  tests](https://docs.pytest.org/en/stable/goodpractices.html#tests-outside-application-code).
- Test files should begin with the `test_` prefix, followed by the module the
  tests cover, for example, a file `foo.py` will have tests in a file
  `test_foo.py`.
  - Tests for `massgov/pfml/api/applications.py` live at `tests/api/test_applications.py`
- Test cases should begin with the `test_` prefix, followed by the function it's
  testing and some description of what about the function it is testing.
  - In `tests/api/test_users.py`, the `test_users_patch_404` function is a test
    (because it begins with `test_`), that covers the `users_patch` function's
    behavior around 404 responses.
  - Tests can be grouped in classes starting with `Test`, methods that start
    with `test_` will be picked up as tests, for example
    `TestFeature::test_scenario`.

There are occasions where tests may not line up exactly with a single source
file, function, or otherwise may need to deviate from this exact structure, but
this is the setup in general.

## conftest files

`conftest.py` files are automatically loaded by pytest, making their contents
available to tests without needing to be imported. They are an easy place to put
shared test fixtures as well as define other pytest configuration (define hooks,
load plugins, define new/override assert behavior, etc.).

They should never be imported directly.

The main `tests/conftest.py` holds widely useful fixtures included for all
tests. Scoped `conftest.py` files can be created that apply only to the tests
below them in the directory hierarchy, for example, the `tests/db/conftest.py`
file is only loaded for tests under `tests/db/`.

More info:
https://docs.pytest.org/en/latest/how-to/fixtures.html?highlight=conftest#scope-sharing-fixtures-across-classes-modules-packages-or-session

## Helpers

If there is useful functionality that needs to be shared between tests, but is
only applicable to testing and is not a fixture, create modules under
`tests/helpers/`.

They can be imported into tests from the path `tests.helpers`, for example,
`from tests.helpers.foo import helper_func`.

## Using Factories

To facilitate easier setup of test data, most database models have factories via
[factory_boy](https://factoryboy.readthedocs.io/) in
`massgov/pfml/db/models/factories.py`.

There are a few different ways of [using the
factories](https://factoryboy.readthedocs.io/en/stable/#using-factories), termed
"strategies": build, create, and stub. Most notably for this project:

- The build strategy via `FooFactory.build()` populates a model class with the
  generated data, but does not attempt to write it to the database
- The create strategy via `FooFactory.create()` writes a generated model to the
  database (can think of it like `FooFactory.build()` then `db_session.add()`
  and `db_session.commit()`)

The build strategy is useful if the code under test just needs the data on the
model and doesn't actually perform any database interactions.

In order to use the create strategy, pull in the `initialize_factories_session`
fixture.

Regardless of the strategy, can override the values for attributes on the
generated models by passing them into the factory call, for example:

```python
FooFactory.build(foo_id=5, name="Bar")
```

would set `foo_id=5` and `name="Bar"` on the generated model, while all other
attributes would use what's configured on the factory class.

For creating a collection of generated models, there are batch methods,
`build_batch()` and `create_batch()`, which will create multiple instances. For
example:

```python
FooFactory.build_batch(size=5)
```

will return 5 `Foo` instances with different data. Attributes set in the batch
call will be shared among all the instances, so:

```python
FooFactory.build_batch(size=2, parent_widget=widget)
```

would create 2 `Foo` instances with `widget` set as their `parent_widget`.

## Integration test marker

An `integration` marker is configured in pytest for the project. Any test that
requires a real database connection or any concrete "resource" outside of the
code itself should be tagged with the `integration` marker. It indicates an
"integration" test, as opposed to a "unit" test, in a somewhat loose sense.

A few common situations are easy cases, if a test is covering API behavior via
fixtures like `app` or `client` or testing state in the database with
`test_db_session`, the test should be marked with `integration`.

Accessing real files is a bit of a gray area. If testing code that needs
file-like objects, should generally prefer using in-memory constructs like
`StringIO` or `BytesIO` to avoid ever touching the filesystem. But currently if
a test needs to load test fixture files or use `tmp_path` to work with a real
file for some purpose, those do not need to be tagged `integration`.

**In the vast majority of cases, the appropriate tests will get automatically tagged with the `integration` marker behind the scenes via the fixtures it uses.**

### Automatic marking

Test fixtures that use real resources should request the fixture
`has_external_dependencies`.

```python
@pytest.fixture
def some_fixture_using_real_resources(has_external_dependencies):
  ...
```

Fixtures that have the `has_external_dependencies` fixture
in their dependency graph do not need to explicitly
request the `has_external_dependencies` fixture.

All tests that request a fixture with `has_external_dependencies`
in their dependency graph will be automatically marked
with the `integration` marker.

### Manual marking

To manually mark integration tests, decorate any individual test
with `@pytest.mark.integration`.

If all (or almost all) tests in a given test file are integration tests, they
can be tagged all at once with a declaration like the following at the top of
the file (after imports):

```python
# every test in here requires real resources
pytestmark = pytest.mark.integration
```

If a test file has a large mix of integration and unit tests that don't make
sense to separate, integration tests can be bundled into a test class which can
then be tagged, for example:

```python
@pytest.mark.integration
class TestIntegrations:
```

(but tagging each individual function with `@pytest.mark.integration` is also
acceptable)
