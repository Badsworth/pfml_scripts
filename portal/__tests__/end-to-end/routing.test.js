const url = `http://localhost:${process.env.PORT}`;

async function launch({ waitForSelector = "#page" }) {
  await page.goto(url);
  await page.waitForSelector(waitForSelector);

  return page;
}

describe("E2E: Routing", () => {
  describe("when user is not authenticated", () => {
    it("loads Log In screen", async () => {
      expect.assertions();

      const headingSelector = "[data-test='sign-in-header-section']";

      await launch({ waitForSelector: headingSelector });
      const heading = await page.$(headingSelector);

      await expect(heading).toMatch("Log in to get started");
    });
  });
});
