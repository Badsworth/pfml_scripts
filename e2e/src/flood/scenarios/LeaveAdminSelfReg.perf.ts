import { StepFunction, TestData, Browser, step, By } from "@flood/element";
import * as Cfg from "../config";
import * as Util from "../helpers";

let emailVerifier: Util.TestMailVerificationFetcher;
let username: string;
let password: string;

export const settings = Cfg.globalElementSettings;
export const scenario: Cfg.LSTScenario = "LeaveAdminSelfRegistration";
export const steps: Cfg.StoredStep[] = [
  {
    time: 15000,
    name: "Go to Employer Registration",
    test: async (browser: Browser): Promise<void> => {
      await browser.page.setCookie({
        name: "_ff",
        value: JSON.stringify({
          pfmlTerriyay: true,
          claimantShowAuth: true,
          employerShowSelfRegistrationForm: true,
        }),
        url: await Cfg.PortalBaseUrl,
      });
      await browser.visit(
        `${await Cfg.PortalBaseUrl}/employers/create-account`
      );
      // const registerEmployerButton = await waitForElement(
      //   browser,
      //   By.linkText("Create an employer account")
      // );
      // await browser.click(registerEmployerButton);
    },
  },
  {
    time: 15000,
    name: "Register new employer",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      // create email verifier and user credentials
      emailVerifier = await Util.getMailVerifier(browser);
      ({ username, password } = emailVerifier.getCredentials());

      const emailInput = await Util.labelled(browser, "Email address");
      await browser.type(emailInput, username);
      const passwordInput = await Util.labelled(browser, "Password");
      await browser.type(passwordInput, password);
      const employerIdInput = await Util.labelled(
        browser,
        "Employer ID number (EIN)"
      );
      await browser.type(
        employerIdInput,
        data.claim.employer_fein ?? "84-7847847"
      );

      const createAccountButton = await Util.waitForElement(
        browser,
        By.css("button[type='submit']")
      );
      await browser.click(createAccountButton);
    },
  },
  {
    time: 15000,
    name: "Verify new employer's email",
    test: async (browser: Browser): Promise<void> => {
      const code = await emailVerifier.getVerificationCodeForUser(username);
      if (code.length === 0) {
        throw new Error("Couldn't getVerificationCodeForUser email!");
      }
      const sixDigitCodeInput = await Util.labelled(browser, "6-digit code");
      await browser.type(sixDigitCodeInput, code);

      const submitButton = await Util.waitForElement(
        browser,
        By.css("button[type='submit']")
      );
      await browser.click(submitButton);
      // wait for successful registration
      await Util.waitForElement(
        browser,
        By.visibleText("Email successfully verified")
      );
    },
  },
  {
    time: 15000,
    name: "Login with new employer account",
    test: async (browser: Browser): Promise<void> => {
      const emailInput = await Util.labelled(browser, "Email address");
      await browser.type(emailInput, username);
      const passwordInput = await Util.labelled(browser, "Password");
      await browser.type(passwordInput, password);
      const logInButton = await Util.waitForElement(
        browser,
        By.css("button[type='submit']")
      );
      await browser.click(logInButton);
      await browser.waitForNavigation();
      const termsButton = await Util.waitForElement(
        browser,
        By.visibleText("Agree and continue")
      );
      await browser.click(termsButton);
      await Util.waitForElement(browser, By.visibleText("Log out"));
    },
  },
];

export default async (): Promise<void> => {
  TestData.fromJSON<Cfg.LSTSimClaim>(
    `../${await Cfg.dataBaseUrl}/claims.json`
  ).filter((line) => line.scenario === scenario);

  steps.forEach((action) => {
    step(action.name, action.test as StepFunction<unknown>);
  });
};
