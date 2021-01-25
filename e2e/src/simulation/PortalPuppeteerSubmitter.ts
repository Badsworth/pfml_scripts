import PortalSubmitter from "./PortalSubmitter";
import puppeteer from "puppeteer";
import delay from "delay";
import AuthenticationManager from "./AuthenticationManager";
import * as actions from "../utils";
import {
  ApplicationRequestBody,
  ApplicationResponse,
  DocumentUploadRequest,
  PaymentPreferenceRequestBody,
} from "../api";
import { Credentials } from "../types";
import { SimulatedEmployerResponse } from "./types";

/**
 * This specialized submitter submits documents through the portal then
 * adjudicates and approves the claim using Puppeteer
 */
export default class PortalPuppeteerSubmitter extends PortalSubmitter {
  fineosBaseURL: string;
  private page?: puppeteer.Page;

  constructor(
    authenticator: AuthenticationManager,
    apiBaseUrl: string,
    fineosBaseUrl: string
  ) {
    super(authenticator, apiBaseUrl);
    this.fineosBaseURL = fineosBaseUrl;
  }

  async submit(
    credentials: Credentials,
    application: ApplicationRequestBody,
    documents: DocumentUploadRequest[] = [],
    paymentPreference: PaymentPreferenceRequestBody = {},
    employerCredentials?: Credentials,
    employerResponse?: SimulatedEmployerResponse
  ): Promise<ApplicationResponse> {
    const submission_result = await super.submit(
      credentials,
      application,
      documents,
      paymentPreference,
      employerCredentials,
      employerResponse
    );
    const { fineos_absence_id } = submission_result;
    if (fineos_absence_id) {
      await this.adjudicateClaim(fineos_absence_id);
    }
    return submission_result;
  }

  private async approveDocuments(page: puppeteer.Page): Promise<void> {
    await actions.clickTab(page, "Evidence");
    while (true) {
      let pendingDocument;
      try {
        pendingDocument = await page.waitForSelector('td[title="Pending"]', {
          timeout: 1000,
        });
      } catch (e) {
        // Break out if there are no pending documents left.
        break;
      }
      await pendingDocument.click();
      await page
        .waitForSelector("input[value='Manage Evidence']")
        .then((el) => el.click());
      await page.waitForSelector(".WidgetPanel_PopupWidget");
      await actions
        .labelled(page, "Evidence Decision")
        .then((el) => el.select("0"));
      await page
        .waitForSelector('.WidgetPanel_PopupWidget input[value="OK"]')
        .then((el) => el.click());
      await page.waitForSelector("#disablingLayer", { hidden: true });
    }
  }

  private async approveCertificationPeriods(
    page: puppeteer.Page
  ): Promise<void> {
    await actions.clickTab(page, "Certification Periods");
    await page
      .waitForSelector('input[value="Prefill with Requested Absence Periods"]')
      .then((el) => el.click());
    await actions.click(
      page,
      await page.waitForSelector("#PopupContainer input[value='Yes']")
    );
  }

  private async adjudicateClaim(fineos_absence_id: string): Promise<void> {
    const page = await this.getPage();
    await page.goto(this.fineosBaseURL);
    await actions.gotoCase(page, fineos_absence_id);
    // Start Adjudication.
    await actions.click(
      page,
      await page.waitForSelector('input[type="submit"][value="Adjudicate"]', {
        visible: true,
      })
    );
    await this.approveDocuments(page);
    await this.approveCertificationPeriods(page);
    // Complete Adjudication.
    await actions.click(
      page,
      await page.waitForSelector("#footerButtonsBar input[value='OK']")
    );
    // Approve the claim.
    await actions.click(
      page,
      await page.waitForSelector(
        "a[title='Approve the Pending Leaving Request']"
      )
    );
  }

  private async getPage(): Promise<puppeteer.Page> {
    if (this.page) {
      return this.page;
    }
    // Viewport must be set so the screen is wide enough to show particular elements, otherwise
    // they are unclickable.
    const browser = await puppeteer.launch({
      defaultViewport: { width: 1200, height: 1000 },
      headless: true,
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
}
