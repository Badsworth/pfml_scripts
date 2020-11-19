import { StepFunction, TestData, Browser, step, By } from "@flood/element";
import {
  globalElementSettings as settings,
  PortalBaseUrl,
  dataBaseUrl,
  LSTSimClaim,
  LSTScenario,
} from "../config";
import {
  getMailVerifier,
  TestMailVerificationFetcher,
  labelled,
  waitForElement,
  waitForRealTimeSim,
} from "../helpers";

let emailVerifier: TestMailVerificationFetcher;
let username: string;
let password: string;

export { settings };
export const scenario: LSTScenario = "PortalRegistration";
export const steps = [
  {
    name: "Visit Portal homepage",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      await browser.page.setCookie({
        name: "_ff",
        value: JSON.stringify({
          pfmlTerriyay: true,
          claimantShowAuth: true,
        }),
        url: await PortalBaseUrl,
      });
      await browser.visit(await PortalBaseUrl);
      await browser.click(await waitForElement(browser, By.linkText("Log in")));
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    },
  },
  {
    name: "Register new user in Portal",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      // create email verifier and user credentials
      emailVerifier = await getMailVerifier(browser);
      ({ username, password } = emailVerifier.getCredentials());
      // go to registration page
      await (
        await waitForElement(browser, By.visibleText("create an account"))
      ).click();
      // fill out the form
      await (await labelled(browser, "Email address")).type(username);
      await (await labelled(browser, "Password")).type(password);
      // submit new user
      await (
        await waitForElement(browser, By.css("button[type='submit']"))
      ).click();
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    },
  },
  {
    name: "Verify new user's email",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      // initial wait time for email to be sent
      const code = await emailVerifier.getVerificationCodeForUser(username);
      if (code.length === 0)
        throw new Error("Couldn't getVerificationCodeForUser email!");
      // type code
      await (await labelled(browser, "6-digit code")).type(code);
      // submit code
      await (
        await waitForElement(browser, By.css("button[type='submit']"))
      ).click();
      // wait for successful registration
      await waitForElement(
        browser,
        By.visibleText("Email successfully verified")
      );
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    },
  },
];

export default (): void => {
  TestData.fromJSON<LSTSimClaim>(`../${dataBaseUrl}/claims.json`).filter(
    (line) => line.scenario === scenario
  );
  steps.forEach((action) => {
    step(action.name, action.test as StepFunction<unknown>);
  });
};
