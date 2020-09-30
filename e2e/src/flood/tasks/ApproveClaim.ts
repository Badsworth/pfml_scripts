import { Browser, By } from "@flood/element";
import { StoredStep } from "../config";
import { waitForElement, labelled } from "../helpers";

export const steps: StoredStep[] = [
  {
    name: "Go to Absence Hub",
    test: async (browser: Browser): Promise<void> => {
      const AbsenceHubTab = await waitForElement(
        browser,
        By.visibleText("Absence Hub")
      );
      await AbsenceHubTab.click();

      const AdjudicateButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Adjudicate']")
      );
      await AdjudicateButton.click();
    },
  },
  {
    name: "Evidence Review",
    test: async (browser: Browser): Promise<void> => {
      const evidenceTab = await waitForElement(
        browser,
        By.visibleText("Evidence")
      );
      await evidenceTab.click();

      const requiredEvidences = await browser.findElements(
        By.css("table[id^='evidenceResultList'] tr")
      );

      for (let i = 0; i < requiredEvidences.length; i++) {
        const evidence = await waitForElement(
          browser,
          By.css(`table[id^='evidenceResultList'] tr:nth-child(${i + 1})`)
        );
        await browser.doubleClick(evidence);

        await browser.wait(1000);
        const manageButton = await waitForElement(
          browser,
          By.css("input[type='submit'][value='Manage Evidence']")
        );
        await manageButton.click();

        const receiptSelect = await labelled(browser, "Evidence Receipt");
        await browser.selectByText(receiptSelect, "Received");

        const decisionSelect = await labelled(browser, "Evidence Decision");
        await browser.selectByText(decisionSelect, "Satisfied");

        const reasonInput = await labelled(browser, "Evidence Decision Reason");
        await browser.type(
          reasonInput,
          "PFMLE2E - Approved for Load and Stress Test purposes"
        );

        const okButton = await waitForElement(
          browser,
          By.css("table[id*='Popup'] input[type='button'][value='OK']")
        );
        await okButton.click();
      }
    },
  },
  {
    name: "Evidence Certification",
    test: async (browser: Browser): Promise<void> => {
      const certificationTab = await waitForElement(
        browser,
        By.visibleText("Certification Periods")
      );
      await certificationTab.click();

      const prefillButton = await waitForElement(
        browser,
        By.css(
          "input[type='submit'][value='Prefill with Requested Absence Periods']"
        )
      );
      await prefillButton.click();

      const yesButton = await waitForElement(
        browser,
        By.css(".popup_buttons input[type='submit'][value='Yes']")
      );
      await yesButton.click();
    },
  },
  {
    name: "Paid Benefits",
    test: async (browser: Browser): Promise<void> => {
      const paidBenefitsTab = await waitForElement(
        browser,
        By.visibleText("Paid Benefits")
      );
      await paidBenefitsTab.click();

      const editButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Edit']")
      );
      await editButton.click();

      const avgWeeklyWage = await labelled(browser, "Average weekly wage");
      await avgWeeklyWage.clear();
      await avgWeeklyWage.type("1000");

      const okButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await okButton.click();
    },
  },
  {
    name: "Accept Leave Plan",
    test: async (browser: Browser): Promise<void> => {
      const ManageRequestTab = await waitForElement(
        browser,
        By.visibleText("Manage Request")
      );
      await ManageRequestTab.click();

      const AcceptButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Accept']")
      );
      await AcceptButton.click();

      const okButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await okButton.click();
    },
  },
  {
    name: "Approve claim",
    test: async (browser: Browser): Promise<void> => {
      /*
      const approveButton = await waitForElement(
        browser,
        By.css("a[aria-label='Approve']")
      );
      await approveButton.click();
      */
      await waitForElement(browser, By.visibleText("Approved"));
    },
  },
];

export default async (browser: Browser, data: unknown): Promise<void> => {
  for (const step of steps) {
    console.log(`Approve - ${step.name}`);
    await step.test(browser, data);
  }
};
