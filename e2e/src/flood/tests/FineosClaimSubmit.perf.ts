import { TestData, Browser, step, By } from "@flood/element";
import { SimulationClaim } from "../../simulation/types";
import {
  globalElementSettings as settings,
  StoredStep,
  getFineosBaseUrl,
  dataBaseUrl,
} from "../config";
import { labelled, waitForElement, formatDate } from "../helpers";
import assert from "assert";

export { settings };
export const scenario = "FineosClaimSubmit";
export const steps: StoredStep[] = [
  {
    name: "Login into fineos",
    test: async (browser: Browser): Promise<void> => {
      await browser.visit(await getFineosBaseUrl());
    },
  },
  {
    name: "Search for a party",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      const { claim } = data as SimulationClaim;
      const linkParties = await waitForElement(
        browser,
        By.css('a[aria-label="Parties"]')
      );
      await linkParties.click();

      assert(claim.tax_identifier, "tax_identifier is not defined");
      const identificationNum = await labelled(
        browser,
        "Identification Number"
      );
      await browser.type(
        identificationNum,
        claim.tax_identifier.split("-").join("")
      );

      const search = await waitForElement(
        browser,
        By.css('input[type="submit"][value="Search"]')
      );
      await search.click();
    },
  },
  {
    name: "Add new application",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      const { claim } = data as SimulationClaim;
      assert(claim.tax_identifier, "tax_identifier is not defined");
      const okButton = await waitForElement(
        browser,
        By.css('input[type="submit"][value="OK"]')
      );
      await okButton.click();
      const addCaseTab = await waitForElement(
        browser,
        By.visibleText("Add Case")
      );
      await addCaseTab.click();
      const selectCase = await waitForElement(
        browser,
        By.css('[title="Absence Case"]')
      );
      await selectCase.click();
      const nextButton = await waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();
    },
  },
  {
    name: "Fill out Intake Opening info",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      const { claim } = data as SimulationClaim;
      const intakeSourceSelect = await labelled(browser, "Intake Source");
      await browser.selectByText(intakeSourceSelect, "Self-Service");
      /* Date of claim submission, defaults to current date/time */
      assert(claim.leave_details, "claim.leave_details is not defined");
      /*
      const notifDateInput = await labelled(browser, "Notification Date");
      await notifDateInput.clear();
      await notifDateInput.type(formatDate(claim.leave_details.employer_notification_date));
      */
      /*
      const notifiedBySelect = await labelled(browser, "Notified By");
      await browser.selectByText(notifiedBySelect, "Employee");
      */
      const nextButton = await waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();
    },
  },
  {
    name: "Fill out Paper Intake - Absence Reason section",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      const { claim } = data as SimulationClaim;
      if (claim.employment_status === "Employed") {
        const absenceRelatesToSelect = await labelled(
          browser,
          "Absence relates to"
        );
        await browser.selectByText(absenceRelatesToSelect, "Employee");
        await browser.wait(1500);
      }

      assert(claim.leave_details, "claim.leave_details is not defined");
      if (claim.leave_details.reason) {
        const absenceReasonSelect = await labelled(browser, "Absence Reason");
        await browser.selectByText(
          absenceReasonSelect,
          claim.leave_details.reason
        );
        await browser.wait(1500);
      }

      // TODO: Handle 2 different qualifiers with single string input from json
      // TODO: use claim.leave_details.reason_qualifier instead of fixed value
      //if (claim.leave_details.reason_qualifier) {
      const firstQualifierSelect = await labelled(browser, "Qualifier 1");
      await browser.selectByText(firstQualifierSelect, "Work Related");
      await browser.wait(1000);

      const secondQualifierSelect = await labelled(browser, "Qualifier 2");
      await browser.selectByText(secondQualifierSelect, "Accident / Injury");
      // await browser.wait(1000);
      //}
    },
  },
  {
    name: "Fill out Paper Intake - Leave Periods section",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      const { claim } = data as SimulationClaim;
      assert(claim.leave_details, "claim.leave_details is not defined");
      assert(
        claim.leave_details.continuous_leave_periods,
        "claim.leave_details.continuous_leave_periods is not defined"
      );
      if (claim.leave_details.continuous_leave_periods.length > 0) {
        const continuousLeave = await waitForElement(
          browser,
          By.css("input[type='checkbox'][id*='continuousTimeToggle_CHECKBOX']")
        );
        await continuousLeave.click();
        await fillContinuousLeavePeriods(browser, data as SimulationClaim);
      }
      await browser.wait(1000);
      // TODO: other types of leaves "Episodic / leave as needed", "Reduced work schedule"
    },
  },
  {
    name: "Fill out Paper Intake - Timely Reporting section",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      const { claim } = data as SimulationClaim;
      assert(claim.leave_details, "claim.leave_details is not defined");
      if (claim.leave_details.employer_notified) {
        const hasBeenNotifiedCheckbox = await labelled(
          browser,
          "Has the Employer been notified?"
        );
        await browser.click(hasBeenNotifiedCheckbox);
        await browser.wait(1500);

        const notifDateInput = await labelled(browser, "Notification Date");
        await notifDateInput.type(
          formatDate(claim.leave_details.employer_notification_date)
        );

        if (claim.leave_details.employer_notification_method) {
          const notifMethodSelect = await labelled(
            browser,
            "Notification Method"
          );
          await browser.selectByText(
            notifMethodSelect,
            claim.leave_details.employer_notification_method
          );
        }
      }
      await browser.wait(1000);
    },
  },
  {
    name: "Submit application",
    test: async (browser: Browser): Promise<void> => {
      const nextButton = await waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();

      const completeRegistration = await waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await completeRegistration.click();

      await waitForElement(browser, By.visibleText("Adjudication"));
    },
  },
];

async function fillContinuousLeavePeriods(
  browser: Browser,
  data: SimulationClaim,
  period = 0
): Promise<void> {
  if (!data.claim.leave_details) return;
  if (!data.claim.leave_details.continuous_leave_periods) return;
  const continuousPeriods = data.claim.leave_details.continuous_leave_periods;
  if (period < continuousPeriods.length) {
    const leavePeriod = continuousPeriods[period];
    const absenceStatusSelect = await labelled(browser, "Absence status");
    await browser.selectByText(
      absenceStatusSelect,
      leavePeriod.is_estimated ? "Estimated" : "Known"
    );

    const startDateInput = await labelled(browser, "Absence start date");
    await browser.type(startDateInput, formatDate(leavePeriod.start_date));
    const endDateInput = await labelled(browser, "Absence end date");
    await browser.type(endDateInput, formatDate(leavePeriod.end_date));
    // TODO: all day ?, last day worked ?, return to work date ?, Time absent ?
    const addButtonLocator = By.css(
      "input[type='button'][id*='AddTimeOffAbsencePeriod'][value='Add']"
    );
    await browser.click(addButtonLocator);
    await browser.wait(1000);
    await browser.click(addButtonLocator);
  }
  // when multiple periods, do recursion
  if (period + 1 < continuousPeriods.length - 1) {
    await browser.wait(1500);
    await fillContinuousLeavePeriods(browser, data, period + 1);
  }
}

export default (): void => {
  TestData.fromJSON<SimulationClaim>(`../${dataBaseUrl}/claims.json`).filter(
    (line) => line.scenario === scenario
  );
  steps.forEach((action) => {
    step(action.name, action.test);
  });

  /* TODO: Employee Section */
  /* TODO: Correspondence Section */
  /* TODO: Contact Details Section */
  /* TODO: Communication Preferences Section */
  /* TODO: Employment Details Section */
  /* TODO: Occupation Details Section */
  /* TODO: Earnings Section */
  /* TODO: Employee Work Pattern Section */

  /* Uncomment to stop test at the end of all steps */
  /* step("Delete me pls", async (browser: Browser) => {
    await browser.wait(Until.elementIsVisible(By.partialVisibleText('pleasestopthanks')))
  }) */
};
