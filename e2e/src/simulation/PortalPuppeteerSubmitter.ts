import PortalSubmitter, { PortalSubmitterOpts } from "./PortalSubmitter";
import { DocumentUploadRequest } from "../api";
import puppeteer from "puppeteer";
import fs from "fs";

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
    const browser = await puppeteer.launch();
    this.page = await browser.newPage();
    return this.page;
  }
  protected async uploadDocuments(
    applicationId: string,
    fineosId: string,
    documents: DocumentUploadRequest[]
  ): Promise<void> {
    const page = await this.getPage();
    await page.goto(`${this.fineosBaseURL}/`);
    await gotoCase(page, fineosId);
    for (const document of documents) {
      await uploadDocument(page, document);
      await createDocumentTask(page);
    }
  }
}

async function gotoCase(page: puppeteer.Page, id: string) {
  await page
    .$(`.menulink a.Link[aria-label="Cases"]`)
    .then((el) => click(page, el));
  await clickTab(page, "Case");
  await labelled(page, "Case Number").then((el) => el.type(id));
  await page
    .$('input[type="submit"][value="Search"]')
    .then((el) => click(page, el));
  const title = await page
    .$(".case_pageheader_title")
    .then((el) => el?.getProperty("innerText").then((val) => val.jsonValue()));
  if (!(typeof title === "string") || !title.match(id)) {
    throw new Error("Page title should include case ID");
  }
}

async function uploadDocument(
  page: puppeteer.Page,
  document: DocumentUploadRequest
) {
  await clickTab(page, "Documents");
  await page
    .waitForSelector('input[type="submit"][value="Add"]')
    .then((el) => click(page, el));

  // Select the document type.
  await clickTab(page, "Search");
  await labelled(page, "Business Type").then((el) =>
    el.type(document.document_type)
  );
  await page
    .$('input[type="submit"][value="Search"]')
    .then((el) => click(page, el));

  const matches = await page.$(`.ListCell[title="${document.document_type}"]`);
  if (!matches) {
    throw new Error("Unable to find document type");
  }
  await page
    .$('input[type="submit"][value="OK"]')
    .then((el) => click(page, el));

  // Upload the file.
  const fileInput = await page.$("input[type=file]");
  fileInput?.uploadFile(
    (document.file as fs.ReadStream).path.toString("utf-8")
  );

  await page
    .$('input[type="submit"][value="OK"]')
    .then((el) => click(page, el));
}

async function createDocumentTask(page: puppeteer.Page) {
  await clickTab(page, "Tasks");
  await page
    .waitForSelector('input[type="submit"][value="Add"]')
    .then((el) => click(page, el));

  await page
    .waitForSelector('input[type="text"][id*="NameTextBox"]')
    .then((el) => el.type("Outstanding Document Received"));
  await page
    .$('input[type="submit"][value="Find"]')
    .then((el) => click(page, el));

  // Issue: there is no way to add a description to the task
  // affects LST and CSR's - won't know which document to review

  await page
    .waitForSelector('input[type="submit"][value="Next"]')
    .then((el) => click(page, el));
}

async function click(
  page: puppeteer.Page,
  element: puppeteer.ElementHandle | null
) {
  if (!element) {
    throw new Error(`No element given`);
  }
  await Promise.all([element.click(), page.waitForNavigation()]);
}

async function clickTab(page: puppeteer.Page, label: string) {
  const tab = await contains(
    page,
    ".TabStrip div.TabOn, .TabStrip div.TabOff",
    label
  );

  // Click the tab, then wait for the tab to have the active class. Once that has been added,
  // we're reasonably sure processing is done.
  await Promise.all([
    tab.click(),
    page.waitForFunction(
      (label) => {
        const tabs = document.querySelectorAll(".TabStrip div.TabOn");
        return (
          Array.prototype.slice
            .call(tabs)
            .filter((tab) => tab.innerHTML.match(label)).length > 0
        );
      },
      undefined,
      [label]
    ),
  ]);
}

async function contains(
  page: puppeteer.Page,
  selector: string,
  text: string
): Promise<puppeteer.ElementHandle> {
  const candidates = await page.$$(selector);
  const checked = [];
  for (const candidate of candidates) {
    const candidateText = await candidate
      .getProperty("innerText")
      .then((val) => val.jsonValue());
    if (text === candidateText) {
      return candidate;
    }
    checked.push(candidateText);
  }
  throw new Error(
    `Unable to find element with selector: ${selector} and text: ${text}. Found: ${checked.join(
      ", "
    )}`
  );
}

async function labelled(
  page: puppeteer.Page,
  label: string
): Promise<puppeteer.ElementHandle> {
  const $label = await contains(page, "label", label);
  const id = await $label.evaluate((el) => el.getAttribute("for"));
  const input = await page.$(`#${id}`);
  if (input !== null) {
    return input;
  }
  throw new Error(`Unable to find input labelled by: ${label}`);
}
