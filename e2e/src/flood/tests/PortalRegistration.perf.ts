import { TestData, Browser, step, By } from "@flood/element";
import { SimulationClaim } from "../../simulation/types";
import { globalElementSettings as settings, PortalBaseUrl } from "../config";
import {
  getMailVerifier,
  TestMailVerificationFetcher,
  labelled,
  waitForElement,
} from "../helpers";

let emailVerifier: TestMailVerificationFetcher;
let username: string;
let password: string;

export { settings };
export const scenario = "PortalRegistration";
export const steps = [
  {
    name: "Visit Portal homepage",
    test: async (browser: Browser): Promise<void> => {
      await browser.page.setCookie({
        name: "_ff",
        value: JSON.stringify({
          pfmlTerriyay: true,
        }),
        url: PortalBaseUrl,
      });
      await browser.visit(PortalBaseUrl);
    },
  },
  {
    name: "Register new user in Portal",
    test: async (browser: Browser): Promise<void> => {
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
    },
  },
  {
    name: "Verify new user's email",
    test: async (browser: Browser): Promise<void> => {
      // TODO: how much do we need to wait
      // for verification email to arrive
      await browser.wait(20000);
      // get the email code
      const code = await emailVerifier.getVerificationCodeForUser(username);
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
    },
  },
];

export default (): void => {
  TestData.fromJSON<SimulationClaim>("../data/pilot3/claims.json").filter(
    (line) => line.scenario === scenario
  );
  steps.forEach((action) => {
    step(action.name, action.test);
  });
};
