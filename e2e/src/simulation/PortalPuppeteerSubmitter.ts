import PortalSubmitter, { PortalSubmitterOpts } from "./PortalSubmitter";
import { DocumentUploadRequest } from "../api";
import puppeteer from "puppeteer";
import fs from "fs";
import delay from "delay";
import * as actions from "../utils";

/**
 * This specialized submitter submits documents through Fineos instead of through the portal.
 */
export default class PortalPuppeteerSubmitter extends PortalSubmitter {
  fineosBaseURL: string;
  private page?: puppeteer.Page;

  constructor(opts: PortalSubmitterOpts, fineosBaseUrl: string) {
    super(opts);
    this.fineosBaseURL = fineosBaseUrl;
  }

  private async getPage(): Promise<puppeteer.Page> {
    if (this.page) {
      return this.page;
    }
    // Viewport must be set so the screen is wide enough to show particular elements, otherwise
    // they are unclickable.
    const browser = await puppeteer.launch({
      defaultViewport: { width: 1200, height: 1000 },
    });
    this.page = await browser.newPage();
    this.page.on("dialog", async (dialog) => {
      // When a dialog is detected, attempt to close it. This is usually
      // a "request in progress" thing, and closing it will allow the rest
      // of the claim to proceed.
      await delay(2000);
      await dialog.dismiss().catch(() => {
        //intentional no-op on error.
      });
    });
    return this.page;
  }
  protected async uploadDocuments(
    applicationId: string,
    fineosId: string,
    documents: DocumentUploadRequest[]
  ): Promise<void> {
    const page = await this.getPage();
    await page.goto(`${this.fineosBaseURL}/`);
    await actions.gotoCase(page, fineosId);
    for (const document of documents) {
      await uploadDocument(page, document);
    }
    for (const document of documents) {
      await createDocumentTask(page, document);
    }
  }
}

async function uploadDocument(
  page: puppeteer.Page,
  document: DocumentUploadRequest
) {
  await actions.clickTab(page, "Documents");
  await page
    .waitForSelector('input[type="submit"][value="Add"]', { visible: true })
    .then((el) => actions.click(page, el));

  // Select the document type.
  await actions.clickTab(page, "Search");
  await actions
    .labelled(page, "Business Type")
    .then((el) => el.type(document.document_type));
  await page
    .$('input[type="submit"][value="Search"]')
    .then((el) => actions.click(page, el));

  // Case insensitive because Fineos task names do not exactly match API task names.
  await page.waitForSelector(`.ListCell[title="${document.document_type}" i]`);
  await page
    .$('input[type="submit"][value="OK"]')
    .then((el) => actions.click(page, el));

  // Upload the file.
  const fileInput = await page.$("input[type=file]");
  await fileInput?.uploadFile(
    (document.file as fs.ReadStream).path.toString("utf-8")
  );

  await page
    .$('input[type="submit"][value="OK"]')
    .then((el) => actions.click(page, el));
}

async function createDocumentTask(
  page: puppeteer.Page,
  document: DocumentUploadRequest
) {
  await actions.clickTab(page, "Tasks");
  await page
    .waitForSelector('input[type="submit"][value="Add"]', { visible: true })
    .then((el) => actions.click(page, el));

  let type = "";
  switch (document.document_type) {
    case "Identification Proof":
      type = "ID Review";
      break;
    case "State Managed Paid Leave Confirmation":
      type = "Certification Review";
      break;
    default:
      throw new Error(`Unknown document type: ${document.document_type}`);
  }
  await page
    .waitForSelector('input[type="text"][id*="NameTextBox"]')
    .then((el) => el.type(type));
  await page
    .$('input[type="submit"][value="Find"]')
    .then((el) => actions.click(page, el));

  await page
    .waitForSelector('input[type="submit"][value="Next"]')
    .then((el) => actions.click(page, el));
}
