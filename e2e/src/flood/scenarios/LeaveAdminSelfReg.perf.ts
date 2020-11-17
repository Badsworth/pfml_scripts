import { StepFunction, TestData, Browser, step, By } from "@flood/element";
import {
  globalElementSettings as settings,
  PortalBaseUrl,
  dataBaseUrl,
  LSTSimClaim,
  LSTScenario,
} from "../config";
import {
  labelled,
  waitForElement,
  getMailVerifier,
  waitForRealTimeSim,
  TestMailVerificationFetcher,
} from "../helpers";

let emailVerifier: TestMailVerificationFetcher;
let username: string;
let password: string;

export { settings };
export const scenario: LSTScenario = "LeaveAdminSelfRegistration";
export const steps = [
  {
    name: "Go to Employer Registration",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      await browser.page.setCookie({
        name: "_ff",
        value: JSON.stringify({
          pfmlTerriyay: true,
        }),
        url: await PortalBaseUrl,
      });
      await browser.visit(await PortalBaseUrl);
      const registerEmployerButton = await waitForElement(
        browser,
        By.linkText("Create an account")
      );
      await browser.click(registerEmployerButton);
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    },
  },
  {
    name: "Register new employer",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      // create email verifier and user credentials
      emailVerifier = await getMailVerifier(browser);
      ({ username, password } = emailVerifier.getCredentials());

      const emailInput = await labelled(browser, "Email address");
      await browser.type(emailInput, username);
      const passwordInput = await labelled(browser, "Password");
      await browser.type(passwordInput, password);
      const employerIdInput = await labelled(browser, "Employer ID number");
      await browser.type(employerIdInput, "84-7847847");

      const createAccountButton = await waitForElement(
        browser,
        By.css("button[type='submit']")
      );
      await browser.click(createAccountButton);
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    },
  },
  {
    name: "Verify new employer's email",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      const code = await emailVerifier.getVerificationCodeForUser(username);
      if (code.length === 0) {
        throw new Error("Couldn't getVerificationCodeForUser email!");
      }
      const sixDigitCodeInput = await labelled(browser, "6-digit code");
      await browser.type(sixDigitCodeInput, code);

      const submitButton = await waitForElement(
        browser,
        By.css("button[type='submit']")
      );
      await browser.click(submitButton);
      // wait for successful registration
      await waitForElement(
        browser,
        By.visibleText("Email successfully verified")
      );
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    },
  },
  {
    name: "Login with new employer account",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      const emailInput = await labelled(browser, "Email address");
      await browser.type(emailInput, username);
      const passwordInput = await labelled(browser, "Password");
      await browser.type(passwordInput, password);
      const logInButton = await waitForElement(
        browser,
        By.css("button[type='submit']")
      );
      await browser.click(logInButton);
      const termsButton = await waitForElement(
        browser,
        By.visibleText("Agree and continue")
      );
      await browser.click(termsButton);
      await waitForElement(browser, By.visibleText("Log out"));
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
