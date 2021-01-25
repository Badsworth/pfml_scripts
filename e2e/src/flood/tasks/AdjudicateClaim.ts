// import { Page } from "puppeteer";
import { Browser, By } from "@flood/element";
import { waitForElement } from "../helpers";
import { LSTSimClaim } from "../config";
import Approve from "./ApproveClaim";

// let mainWindow: Page;
// let popupWindow: Page;
let breakTaskFlow = false;

export default async (browser: Browser, data: LSTSimClaim): Promise<void> => {
  if (breakTaskFlow) return;
  await Approve(browser, data);
};
export const PreAdjudicateAbsence = async (browser: Browser): Promise<void> => {
  const openTask = await waitForElement(
    browser,
    By.css('a[aria-label="Open Task"]')
  );
  await browser.click(openTask);

  try {
    const openClaim = await waitForElement(
      browser,
      By.css('a[title="Navigate to case details"]')
    );
    await browser.click(openClaim);
  } catch (e) {
    // if this task is not attached to any claim, close task
    const closeTask = await waitForElement(
      browser,
      By.css("[title='Close Task']")
    );
    await browser.click(closeTask);
    breakTaskFlow = true;
  }
  // Click 'Do task' button opens a popup window
  // mainWindow = await browser.page;
  // const doTask = await waitForElement(
  //   browser,
  //   By.css('a[aria-label="Do Task"]')
  // );
  // await browser.click(doTask);
  // Waits for new popup window to load
  // and change browser focus to that new tab
  // await browser.wait(5000);
  // popupWindow = await browser.waitForNewPage();
  // await browser.switchTo().page(popupWindow);
  // await browser.setViewport({ width: 1920, height: 1080 });
};

export const PostAdjudicateAbsence = async (): Promise<void> => {
  // Close popup window & go back to initial window
  // await browser.wait(3000);
  // popupWindow.close({ runBeforeUnload: true });
  // await browser.switchTo().page(mainWindow);
};
