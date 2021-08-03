import {
  StepFunction,
  TestData,
  Browser,
  step,
  By,
  Until,
} from "@flood/element";
import * as Cfg from "../config";
import * as Util from "../helpers";
import config from "../../config";
import TestMailVerificationFetcher from "../../submission/TestMailVerificationFetcher";
import { generateCredentials } from "../../util/credentials";

type EmployerData = {
  name: string;
  fein: string;
  withholdings: number[];
};

let username: string;
let password: string;

export const settings = Cfg.globalElementSettings;
export const scenario: Cfg.LSTScenario = "LeaveAdminSelfRegistration";
export const steps: Cfg.StoredStep[] = [
  {
    name: "Go to Employer Registration",
    test: async (browser: Browser): Promise<void> => {
      await browser.page.setCookie({
        name: "_ff",
        value: JSON.stringify({
          pfmlTerriyay: true,
          claimantShowAuth: true,
          employerShowSelfRegistrationForm: true,
          employerAuthThroughApi: true,
          employerShowAddOrganization: true,
          employerShowVerifications: true,
        }),
        url: config("PORTAL_BASEURL"),
      });
      await browser.visit(
        `${config("PORTAL_BASEURL")}/employers/create-account`
      );
    },
  },
  {
    name: "Register new employer",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      // create email verifier and user credentials
      ({ username, password } = generateCredentials());

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
        (data as unknown as EmployerData).fein
      );

      const createAccountButton = await Util.waitForElement(
        browser,
        By.css("button[type='submit']")
      );
      await browser.click(createAccountButton);
    },
  },
  {
    name: "Verify new employer's email",
    test: async (browser: Browser): Promise<void> => {
      const fetcher = new TestMailVerificationFetcher(
        config("TESTMAIL_APIKEY"),
        config("TESTMAIL_NAMESPACE")
      );
      const code = await fetcher.getVerificationCodeForUser(username);
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
  {
    name: "Verify Employer Account",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      const { withholdings, name } = data as unknown as EmployerData;
      const withholding = withholdings.pop();
      if (typeof withholding !== "number") {
        throw new Error("No withholdings given");
      }
      await browser.click(By.linkText("Your organizations"));
      await Util.waitForElement(browser, By.linkText(name)).then((elm) => {
        return elm.click();
      });

      await Util.waitForElement(browser, By.nameAttr("withholdingAmount"));
      await browser.type(
        By.nameAttr("withholdingAmount"),
        withholding.toString()
      );
      await browser.click(Util.byButtonText("Submit"));
      await browser.wait(
        Until.elementIsVisible(
          By.visibleText("Thanks for verifying your paid leave contributions")
        )
      );
      await browser.click(Util.byButtonText("Continue"));
    },
  },
];

export default async (): Promise<void> => {
  TestData.fromJSON<Cfg.LSTSimClaim>(`../data/claims.json`).filter(
    (line) => line.scenario === scenario
  );

  steps.forEach((action) => {
    step(action.name, action.test as StepFunction<unknown>);
  });
};
