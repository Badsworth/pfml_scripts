/**
 * We import from /pure here in order to prevent the auto-cleanup behavior, which
 * attempts to unmount the React tree. This fails for components that initialize
 * USWDS JS, which seems to be due the DOM markup being altered by the USWDS
 * script once the component mounts/unmounts.
 * https://testing-library.com/docs/react-testing-library/setup/#skipping-auto-cleanup
 */
import * as globalStorybookConfig from "storybook/preview";
import { DecoratorFn, Story } from "@storybook/react";
import {
  composeStories,
  setGlobalConfig as setupStorybook,
} from "@storybook/testing-react";
import { render, waitFor } from "@testing-library/react";
import React from "react";
import { axe } from "jest-axe";
import path from "path";
import recursiveReadSync from "recursive-readdir-sync";

setupStorybook({
  ...globalStorybookConfig,
  decorators: globalStorybookConfig.decorators.filter(
    // We need to filter out our next/router setup in Storybook because
    // our tests are already mocking next/router, which breaks this decorator
    (decorator: DecoratorFn) => decorator.name !== "WithNextRouter"
  ),
});

type RelativeFilePath = string;
type AbsoluteFilePath = string;

const STORIES_DIR = "../../storybook/stories/";

// Uncomment and set the relative path of a story, if you want to run only its tests:
const ISOLATED_STORY_PATH = undefined; // `components/core/Button.stories.tsx`;

const storyFilePaths: Array<[RelativeFilePath, AbsoluteFilePath]> =
  recursiveReadSync(path.resolve(__dirname, STORIES_DIR)).map(
    (filePath: string) => [
      // Make the path prettier for the test description:
      path.relative(__dirname, filePath).replace(STORIES_DIR, ""),
      filePath,
    ]
  );

// Axe tests can sometimes take longer than the default 5 seconds
jest.setTimeout(20000);

/**
 * Generated tests for each Storybook story, to ensure our stories are
 * rendering and not showing a blank screen. This doesn't comprehensively
 * test all scenarios that a user can toggle in Storybook, but rather
 * just that the story is rendering *something* for the initial render.
 */
describe("Storybook", () => {
  beforeEach(() => {
    // Failing tests when console.error is called (how things are configured in jest.setup.js)
    // will cause all test suites to fail if one of the tests below fails, so we don't want that.
    // Comment this line for further info when debugging failing tests:
    jest.spyOn(console, "error").mockImplementation();
  });

  const filePathsToTest = storyFilePaths.filter(
    ([relativePath]) =>
      // We currently don't support transforming MDX files in our test suite.
      // Only a few stories are MDX, so we exclude them for now and these
      // will require manual testing by viewing the page in Storybook.
      !relativePath.endsWith(".mdx") &&
      // Allow temporarily isolating a single story file for debugging
      (typeof ISOLATED_STORY_PATH === "undefined" ||
        relativePath === ISOLATED_STORY_PATH)
  );

  // For each Story file, generate a test suite:
  filePathsToTest.forEach(([relativePath, absolutePath]) => {
    describe(`${relativePath}`, () => {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const stories = require(absolutePath);
      const composedStories = composeStories(stories);
      const storyNamesAndComponents = Object.entries(composedStories) as Array<
        [string, Story]
      >;

      // For each story exported from the file, generate a test:
      it.each(storyNamesAndComponents)(
        "renders %s story",
        async (_storyName, StoryComponent) => {
          const { container } = render(<StoryComponent />);

          // Note: argTypes defaultValue is not supported and your story's test
          // is likely to fail. Set the value in args instead.
          // https://github.com/storybookjs/testing-react/issues/56
          await waitFor(() => expect(container).not.toBeEmptyDOMElement());

          const a11yResults = await axe(container);
          expect(a11yResults).toHaveNoViolations();
        }
      );
    });
  });
});
