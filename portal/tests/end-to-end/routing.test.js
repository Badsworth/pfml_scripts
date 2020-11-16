import routes from "../../src/routes";

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
  beforeAll(async () => {
    await launch({ waitForSelector: "h1" });
  });

  it("renders dashboard with login link", async () => {
    expect.assertions();

    const loginLink = await page.waitForSelector("a[href='/login/']");

    expect(loginLink).not.toBeNull();

    await loginLink.click();
    await page.waitForNavigation();
  });

  describe("when user is authenticated", () => {
    beforeAll(async () => {
      const usernameField = await page.$('input[name="username"]');
      const passwordField = await page.$('input[name="password"]');
      const submitButton = await page.$('button[type="submit"]');

      await usernameField.type(cognitoUser.username);
      await passwordField.type(cognitoUser.password);
      await submitButton.click();
      await page.waitForNavigation();
    });

    it("redirects to dashboard", async () => {
      expect.assertions();
      await expect(page.url()).toMatch(`${rootUrl}${routes.claims.dashboard}`);
    });

    describe("when user is on claimant dashboard", () => {
      it("routes to start page when user clicks Create Claim button", async () => {
        expect.assertions();

        const startButton = await page.waitForSelector("a.usa-button");
        await startButton.click();
        await page.waitForNavigation();

        await expect(page.url()).toMatch(`${rootUrl}${routes.claims.start}`);
      });
    });
  });
});
