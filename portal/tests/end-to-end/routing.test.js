const rootUrl = `http://localhost:${process.env.PORT}`;
const cognitoUser = {
  // Nava engineers can view this inbox here: https://groups.google.com/a/navapbc.com/forum/#!forum/mass-pfml-aws-ses
  username: "mass-pfml-aws-ses@navapbc.com",
  password: "{Ey8LsmAZqbu",
};

async function launch({ waitForSelector = "#page" }) {
  await page.goto(rootUrl);
  await page.waitForSelector(waitForSelector);

  return page;
}

describe("E2E: Routing", () => {
  describe("when user is authenticated", () => {
    beforeAll(async () => {
      // Load log in page
      const signInHeaderSelector = "form";
      await launch({ waitForSelector: signInHeaderSelector });

      const usernameField = await page.$('input[name="username"]');
      const passwordField = await page.$('input[name="password"]');
      const submitButton = await page.$('button[type="submit"]');

      await usernameField.type(cognitoUser.username);
      await passwordField.type(cognitoUser.password);
      await submitButton.click();
      await page.waitForNavigation();
    });

    it("starts on dashboard page", async () => {
      expect.assertions();

      await page.waitForSelector("h1");
      const title = await page.$("h1");

      await expect(page.url()).toBe(`${rootUrl}/`);
      await expect(title).toMatch("Get ready to apply");
    });

    describe("when user clicks Create Claim button", () => {
      it("routes to /claim/checklist", async () => {
        expect.assertions();

        const startButton = await page.$("a.usa-button");
        await startButton.click();
        await page.waitForNavigation();

        await expect(page.url()).toMatch(`${rootUrl}/claims/start`);

        const newClaimButton = await page.$("button[name='new-claim']");
        await newClaimButton.click();
        await page.waitForNavigation();

        await expect(page.url()).toMatch(`${rootUrl}/claims/checklist`);
      });
    });
  });
});
