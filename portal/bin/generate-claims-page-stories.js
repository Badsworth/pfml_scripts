/* eslint-disable no-console */
/**
 * @file Node script that generates story files for all the claims page components
 * and puts them in the folder: storybook/stories/pages/applications/autogenerated/.
 * Ignores claims pages that already have a story file defined in
 * storybook/stories/pages/applications/.
 */
const fs = require("fs");
const path = require("path");
const readdirp = require("readdirp");

const customStoriesDir = "storybook/stories/pages/applications";
const autogenStoriesDir = "storybook/stories/pages/applications/autogenerated";

async function main() {
  await generateClaimsPageStories();
}

/**
 * For every claim page component in our source code,
 * check if there is already a custom story file.
 * If not, generate one in the storybook/stories/pages/applications/autogenerated/ folder.
 */
async function generateClaimsPageStories() {
  const claimsPageFiles = await readdirp.promise("src/pages/applications/");
  // Get the subpaths without the extensions
  const claimsPageSubpaths = claimsPageFiles.map((file) =>
    file.path.replace(/.tsx$/, "")
  );
  console.log("Deleting autogenerated folder");
  if (fs.existsSync(autogenStoriesDir)) {
    await fs.promises.rmdir(autogenStoriesDir, { recursive: true });
  }
  await Promise.all(
    claimsPageSubpaths.map(async (claimsPageSubpath) => {
      const customTsStoryPath = `${customStoriesDir}/${claimsPageSubpath}.stories.ts`;
      const customTsxStoryPath = `${customTsStoryPath}x`;
      const autogenStoryPath = `${autogenStoriesDir}/${claimsPageSubpath}.stories.ts`;
      const customStoryExists =
        (await exists(customTsStoryPath)) || (await exists(customTsxStoryPath));
      if (customStoryExists) {
        console.log(
          `Custom story already exists: (${customTsStoryPath}) Skipping`
        );
        return;
      }
      generateStoryFile(autogenStoryPath);
    })
  );
}

/**
 * Generates a story file from the template: claims-page-story.stories.js.tpl
 * @param {string} storyPath Path to the story to generate
 * @returns {Promise}
 */
async function generateStoryFile(storyPath) {
  console.log(`Generating story: ${storyPath}`);
  const dir = path.dirname(storyPath);
  await fs.promises.mkdir(dir, { recursive: true });
  await fs.promises.copyFile(
    "bin/applications-page-story.stories.js.tpl",
    storyPath
  );
}

/**
 * Returns whether a file exists or not
 * @param {string} file File path
 * @returns {Promise<boolean>} Promise resolving to a boolean for whether the file exists or not
 */
async function exists(file) {
  try {
    await fs.promises.access(file, fs.constants.R_OK);
    return true;
  } catch (err) {
    return false;
  }
}

main();