import { Locator, Browser, By, ElementHandle, Until } from "@flood/element";

export const formatDate = (d: string | null | undefined): string => {
  const notificationDate = new Date(d || "");
  const notifDate = {
    day: notificationDate.getDate().toString().padStart(2, "0"),
    month: (notificationDate.getMonth() + 1).toString().padStart(2, "0"),
    year: notificationDate.getFullYear(),
  };
  const notifDateStr = `${notifDate.month}/${notifDate.day}/${notifDate.year}`;
  return notifDateStr;
};

export const labelled = async (
  browser: Browser,
  labelText: string
): Promise<ElementHandle> => {
  const label = By.js(
    (text) =>
      Array.from(document.querySelectorAll("label")).find(
        (label) => label.textContent === text
      ),
    labelText
  );
  const labelEl = await waitForElement(browser, label);
  const inputId = await labelEl.getAttribute("for");
  if (!inputId) {
    throw new Error(
      `Unable to find label with the content: "${labelText}". ${labelEl.toErrorString()}`
    );
  }
  return waitForElement(browser, By.id(inputId));
};

export const waitForElement = async (
  browser: Browser,
  locator: Locator
): Promise<ElementHandle> => {
  await browser.wait(Until.elementIsVisible(locator));
  await browser.focus(locator);
  return browser.findElement(locator);
};
