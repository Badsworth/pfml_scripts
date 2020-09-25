// Expose custom puppeteer matchers (i.e `expect(page).toMatch(...)`)
import "expect-puppeteer";

// Adjust the Jest timeout to account for sometimes slow Network requests (and slow-mo mode)
const timeout = process.env.JEST_PUPPETEER_SLOW_MO
  ? 30000 // 30 seconds to account for intentionally slowed tests
  : 15000; // 15 seconds otherwise

jest.setTimeout(timeout);
