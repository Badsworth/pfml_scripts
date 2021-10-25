# Tests

## Introduction

[Jest](https://jestjs.io/) is used as our JS test runner and is very similar to Jasmine.

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

A test file should be placed in the appropriate `tests` directory (e.g. `admin/tests`) rather than alongside the file it tests. These test files should have the same name as the file they're testing, and have `.test.tsx` as the extension. For example, `pages/index.tsx` and `tests/pages/index.test.tsx`.

## Unit tests

[React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) (RTL) is a testing library used alongside Jest to test React components. It uses DOM Testing Library (DTL) as its core and adds APIs for working with React components. Read the [RTL API documentation](https://testing-library.com/docs/react-testing-library/api) and [DTL documentation](https://testing-library.com/docs/dom-testing-library/api) to learn how to render React components and how to pull information from those React components in order to run test assertions against them.

Along with RTL, the [jest-dom](https://github.com/testing-library/jest-dom) library is used to provide a set of custom jest matchers that extend jest like `.toBeInTheDocument()`, `.toHaveTextContent()`, `.toHaveClass()`, etc.

Below is an example of a React component test:

```js
import React from "react";
import { create } from "react-test-renderer";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Button, { Props as ButtonProps } from "../../src/components/Button";

describe("Button", () => {
  test("button is disabled when disabled prop is true", () => {
    const onClick = jest.fn();
    const props: ButtonProps = {
      disabled: true,
      onClick: onClick,
    };

    render(<Button {...props} />);

    fireEvent.click(screen.getByTestId("button"));

    expect(onClick).toHaveBeenCalledTimes(0);
    expect(screen.getByTestId("button")).toHaveAttribute("disabled");
  });
});
```

### Snapshot tests

[Snapshot tests](https://jestjs.io/docs/en/snapshot-testing) are useful for testing when a React component or JSON output changes unexpectedly. [React test renderer](https://reactjs.org/docs/test-renderer.html) is used with Jest in creating snapshots.

A typical snapshot test case is to render a UI component, take a snapshot, then compares it to the last snapshot that was taken. The test will fail if the two snapshots do not match.

If a snapshot test fails, you should identify whether it failed because the change was unexpected. If it was an unexpected change, then you may have unintentionally broke an expected behavior, in which case you should investigate and fix it before sending the PR out for review. If it failed because you intentionally changed something related to the test, then the snapshot should be updated to reflect the intended change.

To update snapshots, run:

```
npm run test:update-snapshots
```

[Learn more about Snapshot Testing.](https://jestjs.io/docs/en/snapshot-testing)

#### JSON snapshot example

```js
import React from "react";
import { create } from "react-test-renderer";
import Button, { Props as ButtonProps } from "../../src/components/Button";

describe("Button", () => {
  test("test snapshot", () => {
    const props: ButtonProps = {
      onClick: jest.fn(),
    };

    const component = create(<Button {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });
});
```

#### React snapshot example

```js
import React from "react";
import { create } from "react-test-renderer";
import Button, { Props as ButtonProps } from "../../src/components/Button";

describe("Button", () => {
  test("test snapshot", () => {
    const props: ButtonProps = {
      onClick: jest.fn(),
    };

    const component = create(<Button {...props} />);
    expect(component).toMatchSnapshot();
  });
});
```

### Test coverage

Jest includes [built-in support for measuring test coverage](https://jestjs.io/docs/en/cli#coverage), using [Istanbul](https://istanbul.js.org/). The [`coverageReporters`](https://jestjs.io/docs/en/configuration#coveragereporters-array-string) Jest setting can be modified for more advanced test coverage use cases.

To generate and output coverage reports, run:

```
npm run test:coverage
```

The reports will be available in the `/coverage` directory.
