import path from "path";
import recursiveReadSync from "recursive-readdir-sync";

type RelativeFilePath = string;
type AbsoluteFilePath = string;

const SRC_DIR = "../src/";
const STORIES_DIR = "../storybook/stories/";

/**
 * Add a custom matcher so the test failure message is more useful.
 * @see https://jestjs.io/docs/expect#expectextendmatchers
 */
function toNotIncludeJsFiles(filePaths: string[]) {
  const jsFilePaths = filePaths
    .filter((filePath) => filePath.endsWith(".js"))
    .map((filePath) => filePath);

  const failureMessage = () =>
    `expected files to not include .js files. Received these .js files:\n\n${jsFilePaths.join(
      "\n"
    )}`;

  return {
    message: failureMessage,
    pass: jsFilePaths.length === 0,
  };
}

expect.extend({
  toNotIncludeJsFiles,
});

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace jest {
    interface Matchers<R> {
      toNotIncludeJsFiles(): R;
    }
  }
}

describe.each([SRC_DIR, STORIES_DIR])("%s", (targetDir) => {
  it("does not include .js files", () => {
    const filePaths: Array<[RelativeFilePath]> = recursiveReadSync(
      path.resolve(__dirname, targetDir)
    ).map((filePath: AbsoluteFilePath) =>
      // Make the path prettier for the test output:
      path.relative(__dirname, filePath).replace(targetDir, "")
    );

    expect(filePaths).toNotIncludeJsFiles();
  });
});
