/**
 * @file Config options for Jest's Puppeteer integration
 * @see https://github.com/smooth-code/jest-puppeteer
 */

// If JEST_PUPPETEER_CI is set, run the site as part of the test script
const server = process.env.JEST_PUPPETEER_CI
  ? {
      // Use a different port, instead of 3000, in case we're already running the dev server locally.
      // The site should have already been built through a `pre` NPM script
      command: `npm start -- -p ${process.env.PORT}`,
      port: process.env.PORT,
      launchTimeout: 10000,
    }
  : null;

module.exports = {
  launch: {
    // Set JEST_PUPPETEER_HEADLESS to false to turn off headless mode.
    // Results in a browser window opening up for the tests.
    headless: process.env.JEST_PUPPETEER_HEADLESS !== "false",
    // Set JEST_PUPPETEER_SLOW_MO in ms. Slows down Puppeteer operations
    // by the specified amount of milliseconds. Useful so that you can see
    // what is going on. You can start by setting this to 20 and increase
    // it if that's not slow enough to see what you need to see.
    slowMo: process.env.JEST_PUPPETEER_SLOW_MO
      ? process.env.JEST_PUPPETEER_SLOW_MO
      : 0,
  },
  server,
};
