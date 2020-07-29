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

A test file should be placed in the appropriate `tests` directory (e.g. `portal/tests`) rather than alongside the file it tests. These test files should have the same name as the file they're testing, and have `.test.js` as the extension. For example, `pages/index.js` and `tests/pages/index.test.js`.

## Unit tests

[Enzyme](http://airbnb.io/enzyme/) is a test utility used alongside Jest to test React components. Read the [Enzyme documentation](http://airbnb.io/enzyme/) to learn how to Render React components and how to pull information from those React components in order to run test assertions against them.

For simple, stateless components (which hopefully will be most components), you can ["Shallow render"](https://airbnb.io/enzyme/docs/api/shallow.html) the component. Shallow rendering is useful to constrain yourself to testing a component as a unit, and to ensure that your tests aren't indirectly asserting on behavior of child components. It's also helps reduce test suite runtime.

Below is an example of a React component test:

```js
import UploadForm from "./UploadForm";
import { shallow } from "enzyme";

describe("<UploadForm>", () => {
  describe("when the form is submitted", () => {
    it("calls onSubmit", () => {
      const mockSubmit = jest.fn();
      const wrapper = shallow(<UploadForm onSubmit={mockSubmit} />);

      wrapper.simulate("submit");

      expect(mockSubmit).toHaveBeenCalled();
    });
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
it("renders the fields with the expected content and attributes", () => {
  const wrapper = shallow(<UploadFields />);

  // You can output the snapshot to a separate file if its output is verbose:
  expect(wrapper).toMatchSnapshot();
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

## End-to-end tests

End-to-end tests run in a headless Chromium browser.

We use [`jest-puppeteer`](https://github.com/smooth-code/jest-puppeteer) to run our tests using Jest & [Puppeteer](https://developers.google.com/web/tools/puppeteer). This setup exposes Puppeteer's `browser` and `page` as global variables in our test files. In addition, it adds some specific [matchers](https://github.com/smooth-code/jest-puppeteer/blob/master/packages/expect-puppeteer/README.md#api) to make assertions on Puppeteer pages and elements.

Test are ran against the site running on `localhost:3000`. By default, nothing is mocked, so requests will be made to integrations like Cognito and the API. This means that a user account will need manually created in order to test anything behind authentication. Puppeteer can be configured to [intercept requests](https://pptr.dev/#?product=Puppeteer&version=v3.0.4&show=api-pagesetrequestinterceptionvalue) if you don't want a real request to be made.

- [View the `puppeteer` API docs](https://pptr.dev/)
- [View the `expect-puppeteer` API docs](https://github.com/smooth-code/jest-puppeteer/blob/master/packages/expect-puppeteer/README.md#api)

Example:

```js
it("loads page with correct heading", async () => {
  // Open the page. This assumes you're running the server already.
  await page.goto("http://localhost:3000");

  // (Optional) Wait for a specific element to render before proceeding:
  await page.waitForSelector("#page");

  // Find an element on the page
  const heading = await page.$("h1");

  // Assert the heading contains the given text
  await expect(heading).toMatch("Welcome");
});
```

### Debugging headless tests

Debugging headless browser tests can be hard sometimes and it can be useful to pause tests in order to inspect the browser. Jest Puppeteer exposes a method `jestPuppeteer.debug()` that suspends test execution when it is reached and gives you the opportunity to see what's going on in the browser.

#### Puppeteer options

The following environment variables can be set to modify the Puppeteer behavior:

- `JEST_PUPPETEER_HEADLESS` - set to `false` to disable headless mode
- `JEST_PUPPETEER_SLOW_MO`

View [`jest-puppeteer.config.js`](../../portal/jest-puppeteer.config.js) for more info about these options.

Example:

```
JEST_PUPPETEER_HEADLESS=false JEST_PUPPETEER_SLOW_MO=20 npm run test:e2e
```
