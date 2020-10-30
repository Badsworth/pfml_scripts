import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import puppeteer from "puppeteer";
import { getFineosBaseUrl } from "./simulate";
import fs from "fs";
import * as actions from "../../utils";

const cmd: CommandModule<SystemWideArgs, SystemWideArgs> = {
  command: "claim-withdraw",
  describe:
    "Gathers all claims that effect Time Availability and withdraws those claims.",
  async handler(args) {
    args.logger.info("Starting Script");

    const browser = await puppeteer.launch({
      defaultViewport: { width: 1200, height: 1000 },
    });
    const page = await browser.newPage();
    await page.goto(`${getFineosBaseUrl()}/`);
    const em = await getEmployee("financially eligible");
    await goToEmployee(page, em.tax_identifier);
    await goToLeavePeriods(page, args, browser);

    // Gather All Case Number in Table
    await page.waitForTimeout(5000);
    const claimNumbers = await page.$$eval(".PageLinkBeanDescriptor", (links) =>
      links.map((link) => link.innerHTML)
    );

    for (const claimNumber of claimNumbers) {
      if (claimNumber.includes("NTN")) {
        await actions.gotoCase(page, await claimNumber);
        await actions.withdrawClaim(page);
      }
    }

    args.logger.info(
      `Successfully withdrew ${claimNumbers.length - 1} claims!`
    );
    await browser.close();
  },
};

// Supporting Functions
async function goToEmployee(page: puppeteer.Page, employeeSSN: string) {
  await page
    .$(`.menulink a.Link[aria-label="Parties"]`)
    .then((el) => actions.click(page, el));
  await actions
    .labelled(page, "Identification Number")
    .then((el) => el.type(employeeSSN.replace(/-/gi, "")));
  await page
    .$('input[type="submit"][value="Search"]')
    .then((el) => actions.click(page, el));
  await page
    .$('input[type="submit"][value="OK"]')
    .then((el) => actions.click(page, el));
}

async function goToLeavePeriods(
  page: puppeteer.Page,
  args: SystemWideArgs,
  browswer: puppeteer.Browser
): Promise<void> {
  await actions.clickTab(page, "Leave Information");
  await actions.clickTab(page, "Entitlement Periods");
  await page.waitForTimeout(5000);
  const claimAmount = await page
    .$(
      "#entitlementPeriodLeaveRequestListviewWidget_un82_entitlementPeriodLeaveRequestListviewWidget_NumRowsInList"
    )
    .then((el) => el?.getProperty("innerText").then((val) => val.jsonValue()));
  if (claimAmount === "0-0 of 0") {
    args.logger.info("No Claims to Withdraw");
    await browswer.close();
  }
}

async function getEmployee(
  employeeType: string
): Promise<Record<string, string>> {
  const content = await fs.promises.readFile("employee.json");
  return JSON.parse(content.toString("utf-8"))[employeeType];
}

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
