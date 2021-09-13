# Tests

## Introduction

[Jest](https://jestjs.io/) is used as our JS test runner and is very similar to Jasmine.  We also use [jest-dom](https://github.com/testing-library/jest-dom) custom matchers.

**Read the [Jest documentation](https://jestjs.io/en/) to learn how to write assertions.** A good place to start if you are new to JS testing is to learn about [Using Matchers](https://jestjs.io/docs/en/using-matchers).

Below is an example of a test:

```js
import sum from "./sum";

describe("sum", () => {
  it("adds 1 + 2 to equal 3", () => {
    const result = sum(1, 2);

    expect(result).toBe(3);
  });
});
```

## Creating new test files

A test file should be placed in the appropriate `tests` directory (e.g. `portal/tests`) rather than alongside the file it tests. These test files should have the same name as the file they're testing, and have `.test.js` as the extension. For example, `pages/index.js` and `tests/pages/index.test.js`.

**A Migration Note (Sept 2021)**
We are migrating from enzyme to React Test Library. Our enzyme tests live in tests-old/ while we work on migrating. If you're writing new tests, please write them in tests/. Our lint rules enforse that nothing in tests/ can rely on enzyme or anything in tests-old.


## Unit tests

We use [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) alongside Jest. React Testing Library (RTL), enables us to interact with rendered DOM nodes directly in our tests. This helps us to write tests that resemble the way our software is used (more on that in the [RTL guiding principles](https://testing-library.com/docs/guiding-principles)). 

**React Testing Library Resources:**
- [React Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro/)
- [Cheatsheet guide](https://testing-library.com/docs/react-testing-library/cheatsheet/) to reference all the available React Testing Library fucntions
- [Playground](https://testing-playground.com/) to test out your queries

Below is an example of a React component test:

```js
import { fireEvent, render, screen } from "@testing-library/react";
import Button from "./Button";

describe("Button", () => {
  it("is clickable", () => {
    const onClickHandler = jest.fn();
    render(<Button onClick={onClickHandler}>Click me</Button>);
    fireEvent.click(screen.getByText(/Click me/));
    expect(onClickHandler).toHaveBeenCalled();
  });
});
```

### Snapshot tests

[Snapshot tests](https://jestjs.io/docs/en/snapshot-testing) are useful for testing when a React component or JSON output changes unexpectedly.

A typical snapshot test case is to render a UI component, take a snapshot, then compares it to the last snapshot that was taken. The test will fail if the two snapshots do not match.

If a snapshot test fails, you should identify whether it failed because the change was unexpected. If it was an unexpected change, then you may have unintentionally broke an expected behavior, in which case you should investigate and fix it before sending the PR out for review. If it failed because you intentionally changed something related to the test, then the snapshot should be updated to reflect the intended change.

To update snapshots, run:

```
npm run test:update-snapshots
```

[Learn more about Snapshot Testing.](https://jestjs.io/docs/en/snapshot-testing)

#### JSON snapshot example

```js
it("renders the fields with the expected content and attributes", () => {
  const output = callMethodAndReturnJSON();

  // You can use inline snapshots if the output is fairly short:
  expect(output).toMatchInlineSnapshot();
});
```

#### React snapshot example

```js
it("renders the component as expected", () => {
    const { container } = render(<ExampleComponent />);

    expect(container.firstChild).toMatchSnapshot();
  });
```

### Mocks

Mock functions make it easy to test the links between code by erasing the actual implementation of a function, capturing calls to the function (and the parameters passed in those calls), capturing instances of constructor functions when instantiated with new, and allowing test-time configuration of return values.

The quickest way to mock a module is to call `jest.mock('MODULE_NAME_HERE')` at the top of your test file.

To create a manual mock of a Node module, create a file in a top-level `__mocks__` directory.

You can also create a Mock function/spy using `jest.fn()`

[Learn more about Mock Functions](https://jestjs.io/docs/en/mock-functions).

### Test coverage

Jest includes [built-in support for measuring test coverage](https://jestjs.io/docs/en/cli#coverage), using [Istanbul](https://istanbul.js.org/). The [`coverageReporters`](https://jestjs.io/docs/en/configuration#coveragereporters-array-string) Jest setting can be modified for more advanced test coverage use cases.
