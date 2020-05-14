// Expose custom puppeteer matchers (i.e `expect(page).toMatch(...)`)
import "expect-puppeteer";

// Adjust the Jest timeout to account for slow-mo
const timeout = process.env.JEST_PUPPETEER_SLOW_MO
  ? 30000 // 30 seconds to account for intentionally slowed tests
  : 10000; // 10 seconds otherwise

jest.setTimeout(timeout);
