import fs from "fs";
import stringify from "csv-stringify";
import parse from "csv-parse";
import path from "path";
import puppeteer from "puppeteer";
import delay from "delay";
import { CommandModule } from "yargs";
import SimulationStorage from "../SimulationStorage";
import { SystemWideArgs } from "../../cli";
import * as actions from "../../utils";
import { getFineosBaseUrl } from "./simulate";

type ExtractPaymentDataArgs = {
  directory: string;
} & SystemWideArgs;

interface ReportRecord {
  fineos_case: string;
  scenario: string;
}

const cmd: CommandModule<SystemWideArgs, ExtractPaymentDataArgs> = {
  command: "extractPaymentData",
  describe:
    "Generate a csv file that lists payments for claims from report.csv",
  builder: {
    directory: {
      type: "string",
      description: "The directory with existing an existing report.csv file",
      demandOption: true,
      requiresArg: true,
      normalize: true,
      alias: "d",
    },
  },
  async handler(args) {
    args.logger.info("Starting extraction of payment information");
    const storage = new SimulationStorage(args.directory);

    const rows = [];

    const browser = await puppeteer.launch({
      defaultViewport: { width: 1200, height: 1000 },
      headless: false,
    });
    const page = await browser.newPage();
    page.on("dialog", async (dialog) => {
      // When a dialog is detected, attempt to close it. This is usually
      // a "request in progress" thing, and closing it will allow the rest
      // of the claim to proceed.
      await delay(2000);
      await dialog.dismiss().catch(() => {
        //intentional no-op on error.
      });
    });
    await page.goto(getFineosBaseUrl());

    const reportRecords = await getReportRecords(storage);
    for (const reportRecord of reportRecords) {
      const fineos_absence_id = reportRecord["fineos_case"];
      const scenario = reportRecord["scenario"];

      try {
        await actions.gotoCase(page, fineos_absence_id);
        await actions
          .contains(page, ".tabset a", "Absence Paid Leave Case")
          .then((el) => actions.click(page, el))
          .catch((e) => {
            console.log(
              `No absence paid leave case found for case ${fineos_absence_id}: ${e.message}`
            );
          });
        await actions.clickTab(page, "Financials");
        await actions.clickTab(page, "Payment History");
        // For each active payment, click on it, click view, get details, click
        // close.
        const activePayments = await page.$$(
          'Table[id*="PaymentHistoryDetailsListviewWidget"] tr td[title="Active"]'
        );
        if (activePayments.length === 0) {
          continue;
        }
        for (let i = 0; i < activePayments.length; i++) {
          await actions.click(page, activePayments[i]);
          await page
            .$('input[id*="PaymentHistoryDetailsListviewWidget"][value="View"]')
            .then((el) => actions.click(page, el));
          const paymentDetails = await getPaymentDetails(
            page,
            fineos_absence_id,
            scenario
          );
          rows.push(paymentDetails);
        }
      } catch (e) {
        args.logger.error(e);
      }
    }
    await writePaymentDetails(rows, storage);
    await browser.close();
  },
};

export async function getReportRecords(
  storage: SimulationStorage
): Promise<Array<ReportRecord>> {
  const records = [];
  const parser = fs
    .createReadStream(path.join(storage.directory, "report.csv"))
    .pipe(
      parse({
        columns: [
          "unique_id",
          "scenario",
          "first_name",
          "last_name",
          "ssn",
          "fein",
          "fineos_case",
          "yearly_wages",
          "error_message",
        ],
        from_line: 2,
      })
    );

  for await (const record of parser) {
    records.push(record);
  }
  return records;
}

export function writePaymentDetails(
  rows: Array<{ [key: string]: string }>,
  storage: SimulationStorage
): void {
  stringify(
    rows,
    {
      header: true,
    },
    function (err, output) {
      if (typeof output === "string") {
        fs.writeFileSync(
          path.join(storage.directory, "paymentDetails.csv"),
          output
        );
      }
    }
  );
}

export async function getPaymentDetails(
  page: puppeteer.Page,
  fineos_absence_id: string,
  scenario: string
): Promise<{ [key: string]: string }> {
  const paymentDetails: { [key: string]: string } = {
    case: fineos_absence_id,
    scenario: scenario,
  };
  const attributes = [
    "Net Amount",
    "Issue Date",
    "Transaction Status Date",
    "Transaction Number",
    "Stock Number",
    "Transaction Status",
    "Extraction Date",
    "Payment Method",
    "Address",
  ];
  for (const attribute of attributes) {
    const label = await actions.contains(
      page,
      "div.TabPanel table.WidgetPanel tr label.TextLabel",
      attribute
    );
    const value = await (
      await page.evaluateHandle(
        (el) => el.parentNode.parentNode.nextElementSibling.innerText,
        label
      )
    ).jsonValue();
    if (typeof value === "string") {
      paymentDetails[attribute] = value;
    }
  }
  return paymentDetails;
}

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
