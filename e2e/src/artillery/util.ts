import { chromium } from "playwright-chromium";
import assert from "assert";
import config from "../../src/config";
import winston from "winston";

export type UsefulClaimData = {
  id: string;
  scenario: string;
  first_name?: string | null;
  last_name?: string | null;
  tax_identifier?: string | null;
  employer_fein?: string | null;
};

export function getDataFromClaim(
  claim: GeneratedClaim | undefined
): UsefulClaimData {
  if (!claim) {
    throw new Error("No claim");
  }
  const { tax_identifier, employer_fein, first_name, last_name } = claim.claim;
  return {
    id: claim.id,
    scenario: claim.scenario,
    first_name,
    last_name,
    tax_identifier,
    employer_fein,
  };
}

export async function checkClaimStatus(
  fineosID: string,
  claimaintCreds: Credentials,
  logger: winston.Logger,
  debug = false
): Promise<void> {
  const browser = await chromium.launch({
    headless: !debug,
    slowMo: debug ? 100 : undefined,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
  });
  const context = await browser.newContext({
    viewport: { width: 1200, height: 1000 },
  });
  context.addCookies([
    {
      name: "_ff",
      value: JSON.stringify({
        pfmlTerriyay: true,
        noMaintenance: true,
        employerShowDashboardSearch: true,
        employerShowReviewByStatus: true,
        claimantShowStatusPage: true,
      }),
      url: config("PORTAL_BASEURL"),
    },
  ]);
  const page = await context.newPage();
  logger.debug("Logging into claimant portal");
  await page.goto(`${config("PORTAL_BASEURL")}/login`);
  await page.waitForLoadState("networkidle");
  await page.fill(
    "input[type='email'][name='username']",
    claimaintCreds.username
  );
  await page.fill(
    "input[type='password'][name='password']",
    claimaintCreds.password
  );
  await page.click("button[type='submit']");
  await page.waitForNavigation();
  logger.debug("Navigating to status page ...");
  await page.goto(
    `${config(
      "PORTAL_BASEURL"
    )}/applications/status/?absence_case_id=${fineosID}`
  );
  const status = await page.innerText(".measure-6 .margin-top-2 .usa-tag");
  logger.debug("Confirming Status");
  assert.strictEqual(status, "PENDING");
  await page.click(
    `a[href='/applications/upload/?absence_case_id=${fineosID}']`
  );
  await page.check("label[class='usa-radio__label'][for='InputChoice2']");
  await page.waitForLoadState("networkidle");
  await page.click("button[type='submit']");
  await browser.close();
  logger.info("Claimant Status Page Check Complete!");
}
