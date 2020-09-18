import { TestSettings, TestData, Browser, step, By } from "@flood/element";
import { SimulationClaim } from "../../simulation/types";
import {
  PortalBaseUrl,
  APIBaseUrl,
  getRequestOptions,
  config,
} from "../config";
import { labelled, waitForElement } from "../helpers";

export const settings: TestSettings = {
  actionDelay: 0.01,
  stepDelay: 0.01,
  loopCount: 1,
  waitUntil: "visible",
  userAgent: "PFML Load Test Bot",
  description: "PFML Load Test Bot",
  screenshotOnFailure: true,
  disableCache: false,
  clearCache: false,
  clearCookies: false,
};

let authToken: string;
let applicationId: string;
export const scenario = "APIPOC";
export const steps = [
  {
    name: "Login in Portal",
    test: async (browser: Browser): Promise<void> => {
      // Fetch an auth token by performing a browser-based login.
      await browser.page.setCookie({
        name: "_ff",
        value: JSON.stringify({
          pfmlTerriyay: true,
        }),
        url: PortalBaseUrl,
      });
      await browser.visit(PortalBaseUrl);
      await (await labelled(browser, "Email address")).type(
        await config("PORTAL_USERNAME")
      );
      await (await labelled(browser, "Password")).type(
        await config("PORTAL_PASSWORD")
      );
      await (
        await waitForElement(browser, By.css("button[type='submit']"))
      ).click();
      await waitForElement(browser, By.visibleText("Log out"));
      const cookie = (await browser.page.cookies()).find((cookie) => {
        return cookie.name.match(
          /CognitoIdentityServiceProvider\..*\.accessToken/
        );
      });
      if (!cookie) {
        throw new Error("Unable to find accessToken cookie");
      }
      authToken = cookie.value;
    },
  },
  {
    name: "Create a new application",
    test: async (browser: Browser): Promise<void> => {
      const reqOptions = getRequestOptions(authToken, "POST");
      const res = await browser.evaluate(
        (baseUrl, options) => {
          return new Promise((resolve, reject) => {
            fetch(`${baseUrl}/applications`, options)
              .then((r) => {
                resolve(r.json());
              })
              .catch(reject);
          });
        },
        APIBaseUrl,
        reqOptions
      );
      if (!res.data || !res.data.application_id) {
        throw new Error(`Unable to create application: ${JSON.stringify(res)}`);
      }
      applicationId = res.data.application_id;
      console.log("Created application", applicationId);
    },
  },
  {
    name: "Update application",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      const reqOptions = getRequestOptions(
        authToken,
        "PATCH",
        (data as SimulationClaim).claim
      );
      const res = await browser.evaluate(
        (baseUrl, appId, options) => {
          return new Promise((resolve, reject) => {
            fetch(`${baseUrl}/applications/${appId}`, options)
              .then((r) => {
                resolve(r.json());
              })
              .catch(reject);
          });
        },
        APIBaseUrl,
        applicationId,
        reqOptions
      );
      if (res.status_code !== 200) {
        throw new Error(`Unable to update application: ${JSON.stringify(res)}`);
      }
      console.log("Updated application", res.status_code);
    },
  },
  {
    name: "Submit application",
    test: async (browser: Browser): Promise<void> => {
      await browser.visit(PortalBaseUrl);
      /* We don't want to actually create claims at this initial stage */
      /* const reqOptions = getRequestOptions(authToken, "POST");
      const res = await browser.evaluate((baseUrl, appId, options) => {
        return new Promise((resolve, reject) => {
          fetch(`${baseUrl}/applications/${appId}/submit_application`, options)
            .then((r) => {
              resolve(r.json());
            }).catch(reject)
        });
      }, APIBaseUrl, applicationId, reqOptions)
      if (res.status_code !== 503) {
        throw new Error(`Unable to update application: ${JSON.stringify(res)}`);
      }
      console.log("Submitted application", res);
      */
    },
  },
];

export default (): void => {
  TestData.fromJSON<SimulationClaim>("../data/claims.json").filter(
    (line) => line.scenario === scenario
  );
  steps.forEach((action) => {
    step(action.name, action.test);
  });
};
