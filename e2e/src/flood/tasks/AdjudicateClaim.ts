import { Page } from "puppeteer";
import { Browser, By } from "@flood/element";
import { LSTSimClaim } from "../config";
import { waitForElement } from "../helpers";
import Approve from "./ApproveClaim";
import Deny from "./DenyClaim";

let mainWindow: Page;
let popupWindow: Page;

export default async (browser: Browser, data: LSTSimClaim): Promise<void> => {
  const decideStep = Math.random() > 0.5 ? Approve : Deny;
  await decideStep(browser, data);
};

export const PreAdjudicateAbsence = async (browser: Browser): Promise<void> => {
  // Click 'Do task' button opens a popup window
  mainWindow = await browser.page;
  const doTask = await waitForElement(
    browser,
    By.css('a[aria-label="Do Task"]')
  );
  await browser.click(doTask);
  // Waits for new popup window to load
  // and change browser focus to that new tab
  await browser.wait(5000);
  popupWindow = await browser.waitForNewPage();
  await browser.switchTo().page(popupWindow);
  await browser.setViewport({ width: 1920, height: 1080 });
};

export const PostAdjudicateAbsence = async (
  browser: Browser
): Promise<void> => {
  // Close popup window & go back to initial window
  await browser.wait(3000);
  popupWindow.close({ runBeforeUnload: true });
  await browser.switchTo().page(mainWindow);
};
