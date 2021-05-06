import { StepFunction, TestData, Browser, step, By, ENV } from "@flood/element";
import * as Cfg from "../config";
import * as Util from "../helpers";
import assert from "assert";

let fineosId: string;
let claimType: Cfg.ClaimType;

export const settings = {
  ...Cfg.globalElementSettings,
  stepDelay: 1,
  actionDelay: 1,
};
export const scenario: Cfg.LSTScenario = "FineosClaimSubmit";
export const steps: Cfg.StoredStep[] = [
  {
    time: 15000,
    name: "Login into fineos",
    test: async (browser: Browser): Promise<void> => {
      await browser.visit(await Cfg.getFineosBaseUrl("SAVILINX"));
    },
  },
  {
    time: 15000,
    name: "Search for a party",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      const { claim } = data;
      const linkParties = await Util.waitForElement(
        browser,
        By.css('a[aria-label="Parties"]')
      );
      await linkParties.click();

      assert(claim.tax_identifier, "tax_identifier is not defined");
      const identificationNum = await Util.labelled(
        browser,
        "Identification Number"
      );
      await browser.type(
        identificationNum,
        claim.tax_identifier.split("-").join("")
      );

      const search = await Util.waitForElement(
        browser,
        By.css('input[type="submit"][value="Search"]')
      );
      await search.click();
      const okButton = await Util.waitForElement(
        browser,
        By.css('input[type="submit"][value="OK"]')
      );
      await okButton.click();
    },
  },
  {
    time: 15000,
    name: "Fill out Notification Details",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      const { claim } = data;
      const createNotif = await Util.waitForElement(
        browser,
        By.visibleText("Create Notification")
      );
      await createNotif.click();

      const notifSourceSelect = await Util.labelled(
        browser,
        "Notification source"
      );
      await browser.selectByText(notifSourceSelect, "Self-Service");
      /* Date of claim submission, defaults to current date/time */
      assert(claim.leave_details, "claim.leave_details is not defined");
      const notifDateInput = await Util.labelled(browser, "Notification date");
      await notifDateInput.clear();
      await notifDateInput.type(
        Util.formatDate(claim.leave_details.employer_notification_date)
      );

      const notifiedBySelect = await Util.labelled(browser, "Notified by");
      await browser.selectByText(notifiedBySelect, "Requester");

      const nextButton = await Util.waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();
    },
  },
  {
    time: 15000,
    name: "Fill out Occupation Details",
    test: async (browser: Browser): Promise<void> => {
      const nextButton = await Util.waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();
    },
  },
  {
    time: 15000,
    name: "Fill out Notification Options",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      const {
        claim: { leave_details },
      } = data;
      switch (leave_details?.reason) {
        case "Serious Health Condition - Employee":
          claimType = Cfg.ClaimType.ACCIDENT;
          break;
        case "Pregnancy/Maternity":
          claimType = Cfg.ClaimType.PREGNANCY;
          break;
        case "Child Bonding":
          claimType = Cfg.ClaimType.BONDING;
          break;
        default:
          throw new Error(
            `There is no claim type matching '${leave_details?.reason}'`
          );
      }
      const claimTypeRadio = await Util.waitForElement(
        browser,
        By.css(
          `[type='radio'][value*='notificationReasonRadio928000${claimType}']`
        )
      );
      await claimTypeRadio.click();

      const nextButton = await Util.waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();
    },
  },
  {
    time: 15000,
    name: "Fill out Reason for Absence",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      const { claim } = data;
      const { leave_details } = claim;

      const absenceRelatesToSelect = await Util.labelled(
        browser,
        "Absence relates to"
      );
      const relatesTo =
        claimType === Cfg.ClaimType.ACCIDENT
          ? "Employee"
          : claimType === Cfg.ClaimType.BONDING
          ? "Family"
          : "";
      await browser.selectByText(absenceRelatesToSelect, relatesTo);

      if (leave_details?.reason) {
        const absenceReasonSelect = await Util.labelled(
          browser,
          "Absence reason"
        );
        await browser.selectByText(absenceReasonSelect, leave_details?.reason);
        await browser.wait(1000);
        if (
          claimType === Cfg.ClaimType.ACCIDENT ||
          leave_details?.reason_qualifier
        ) {
          const firstQualifierSelect = await Util.labelled(
            browser,
            "Qualifier 1"
          );
          await browser.selectByText(
            firstQualifierSelect,
            claimType === Cfg.ClaimType.ACCIDENT
              ? "Work Related"
              : (leave_details?.reason_qualifier as string)
          );
          await browser.wait(1000);
        }
      }

      /* currently no longer necessary, but might be later
      if (claimType !== ClaimType.ACCIDENT && leave_details?.reason_qualifier) {
        const secondQualifierSelect = await Util.labelled(browser, "Qualifier 2");
        await browser.selectByText(
          secondQualifierSelect,
          leave_details?.reason_qualifier
        );
      } */

      if (claimType === Cfg.ClaimType.BONDING) {
        const relationshipSelect = await Util.labelled(
          browser,
          "Primary Relationship to Employee"
        );
        await browser.selectByText(
          relationshipSelect,
          leave_details?.caring_leave_metadata?.relationship_to_caregiver ??
            "Child"
        );
        await browser.wait(1000);

        const relFirstQualifierSelect = await Util.waitForElement(
          browser,
          By.css(
            "#leaveRequestAbsenceRelationshipsWidget select[name*='selected-qualifier1']"
          )
        );
        const relQualifier1 =
          leave_details?.caring_leave_metadata?.relationship_to_caregiver ??
          leave_details?.reason_qualifier === "Foster Care"
            ? "Foster"
            : leave_details?.reason_qualifier === "Adoption"
            ? "Adopted"
            : "Biological";
        await browser.selectByText(relFirstQualifierSelect, relQualifier1);
        await browser.wait(1000);
      }
      const nextButton = await Util.waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();
    },
  },
  {
    time: 15000,
    name: "Fill out Dates of Absence",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      const { claim } = data;
      assert(claim.leave_details, "claim.leave_details is not defined");
      assert(
        claim.leave_details.continuous_leave_periods,
        "claim.leave_details.continuous_leave_periods is not defined"
      );
      if (claim.has_continuous_leave_periods) {
        const continuousLeave = await Util.waitForElement(
          browser,
          By.css("input[type='checkbox'][id*='continuousTimeToggle_CHECKBOX']")
        );
        await continuousLeave.click();
        await fillContinuousLeavePeriods(browser, data);
      }
      await browser.wait(1000);
      const nextButton = await Util.waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();
      // TODO: other types of leaves "Episodic / leave as needed", "Reduced work schedule"
    },
  },
  {
    time: 15000,
    name: "Fill out Work Absence Details",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      const { claim } = data;
      const { work_pattern, leave_details } = claim;
      if (work_pattern?.work_pattern_type) {
        const workPatternTypeSelect = await Util.labelled(
          browser,
          "Work Pattern Type"
        );
        await browser.selectByText(
          workPatternTypeSelect,
          work_pattern?.work_pattern_type
        );
      }
      if (work_pattern?.work_week_starts) {
        const workWeekStartsSelect = await Util.labelled(
          browser,
          "Work Week Starts"
        );
        await browser.selectByText(
          workWeekStartsSelect,
          work_pattern?.work_week_starts
        );
      }
      if (work_pattern?.work_pattern_days?.length) {
        let dayIdx = 0;
        for (const day of work_pattern?.work_pattern_days) {
          dayIdx++;
          if (!day.minutes || day.minutes === 0) continue;
          const hoursInput = await Util.waitForElement(
            browser,
            By.css(`.workPattern td:nth-child(${dayIdx}) input[id*='hours']`)
          );
          await browser.clear(hoursInput);
          await browser.type(
            hoursInput,
            Math.floor(day.minutes / 60).toString()
          );
          if (day.minutes % 60 > 0) {
            const minutesInput = await Util.waitForElement(
              browser,
              By.css(
                `.workPattern td:nth-child(${dayIdx}) input[id*='minutes']`
              )
            );
            await browser.clear(minutesInput);
            await browser.type(minutesInput, (day.minutes % 60).toString());
          }
        }
        const applyWorkPatternButton = await Util.waitForElement(
          browser,
          By.css('input[type="submit"][value="Apply to Calendar"]')
        );
        await applyWorkPatternButton.click();
      }

      if (leave_details?.employer_notified) {
        const hasBeenNotifiedCheckbox = await Util.labelled(
          browser,
          "Has the Employer been notified?"
        );
        await browser.click(hasBeenNotifiedCheckbox);
        await browser.wait(1500);

        const notifDateInput = await Util.labelled(
          browser,
          "Notification Date"
        );
        await notifDateInput.type(
          Util.formatDate(leave_details?.employer_notification_date)
        );

        if (leave_details?.employer_notification_method) {
          const notifMethodSelect = await Util.labelled(
            browser,
            "Notification Method"
          );
          await browser.selectByText(
            notifMethodSelect,
            leave_details?.employer_notification_method
          );
        }
      }
      const nextButton = await Util.waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();
    },
  },
  {
    time: 15000,
    name: "Fill out Additional Absence Details",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      const { claim } = data;
      const { leave_details } = claim;
      if (claimType === Cfg.ClaimType.BONDING) {
        // no Family member's First Name specified in SimulationClaim?
        const firstNameInput = await Util.labelled(browser, "First Name");
        await browser.type(firstNameInput, claim.first_name ?? "Thisis");
        // no Family member's Last Name specified in SimulationClaim?
        const lastNameInput = await Util.labelled(browser, "Last Name");
        await browser.type(lastNameInput, claim.last_name ?? "Mychild");

        if (leave_details?.child_birth_date) {
          const dateOfBirthInput = await Util.labelled(
            browser,
            "What is your Family Member's Date of Birth?"
          );
          await browser.type(
            dateOfBirthInput,
            Util.formatDate(leave_details?.child_birth_date)
          );
        }
        // no Family member's gender specified in SimulationClaim?
        const genderSelect = await Util.labelled(
          browser,
          "What is your Family Member's Gender?"
        );
        await browser.selectByText(genderSelect, "Not Provided");

        if (
          claimType === Cfg.ClaimType.BONDING &&
          leave_details?.reason_qualifier === "Foster Care"
        ) {
          if (leave_details?.child_placement_date) {
            const dateOfPlacementInput = await Util.labelled(
              browser,
              "What is the date of placement, if applicable?"
            );
            await browser.type(
              dateOfPlacementInput,
              Util.formatDate(leave_details?.child_placement_date)
            );
          }
          if (
            leave_details?.continuous_leave_periods?.length &&
            leave_details?.child_birth_date
          ) {
            const willBe18Select = await Util.labelled(
              browser,
              "Will your family member be 18 years or older on the start date of the leave request?"
            );
            let startDate = new Date(
              leave_details?.continuous_leave_periods[0].start_date as string
            );
            startDate = new Date(
              startDate.getFullYear() - 18,
              startDate.getMonth(),
              startDate.getDate()
            );
            const willNotBe18 =
              startDate <= new Date(leave_details?.child_birth_date);
            await browser.selectByText(
              willBe18Select,
              willNotBe18 ? "No" : "Yes"
            );
          }
        }
      }
      const nextButton = await Util.waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();
    },
  },
  {
    time: 15000,
    name: "Complete Wrap up section",
    test: async (browser: Browser): Promise<void> => {
      const nextButton = await Util.waitForElement(
        browser,
        By.css('input[type="submit"][value^="Next"]')
      );
      await nextButton.click();

      const notifStatus = await (
        await Util.waitForElement(browser, By.css("dl.status dd"))
      ).text();
      assert(
        notifStatus.includes("Open"),
        `Notification Status is '${notifStatus}' instead of 'Open'.`
      );
    },
  },
  {
    time: 15000,
    name: "Upload documents",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      const { documents } = data;
      fineosId = (await (
        await Util.waitForElement(
          browser,
          By.css(".sitemapNodeSelected + .sitemapNode")
        )
      ).getAttribute("id")) as string;
      const gotoClaim = await Util.waitForElement(
        browser,
        By.css(".sitemapNodeSelected + .sitemapNode a")
      );
      await browser.click(gotoClaim);
      const documentsTab = await Util.waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='11']")
      );
      await browser.click(documentsTab);
      for (const doc of documents) {
        const addDocument = await Util.waitForElement(
          browser,
          By.css("input[type='submit'][title='Add Document']")
        );
        await browser.click(addDocument);
        const searchTab = await Util.waitForElement(
          browser,
          By.css("[class^='TabO'][keytipnumber='4']")
        );
        await browser.click(searchTab);
        // search for doc type
        const docType = await Util.labelled(browser, "Business Type");
        await browser.type(docType, doc.document_type);
        const searchButton = await Util.waitForElement(
          browser,
          By.css("input[type='submit'][value='Search']")
        );
        await browser.click(searchButton);
        const searchOkButton = await Util.waitForElement(
          browser,
          By.css("input[type='submit'][value='OK']")
        );
        await browser.click(searchOkButton);
        // upload pdf
        const uploadInput = await Util.waitForElement(
          browser,
          By.css("#uploadpath")
        );
        await uploadInput.uploadFile("forms/hcp-real.pdf");
        const uploadOkButton = await Util.waitForElement(
          browser,
          By.css("input[type='submit'][value='OK']")
        );
        await browser.click(uploadOkButton);
      }
    },
  },
  {
    time: 0,
    name: "Assign tasks to specific Agent",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      if (!ENV.FLOOD_LOAD_TEST) {
        const assignTasksStep = Util.assignTasks(fineosId);
        console.info(assignTasksStep.name);
        await assignTasksStep.test(browser, data);
      }
    },
  },
];

async function fillContinuousLeavePeriods(
  browser: Browser,
  data: Cfg.LSTSimClaim,
  period = 0
): Promise<void> {
  if (!data.claim.leave_details) return;
  if (!data.claim.leave_details.continuous_leave_periods) return;
  const continuousPeriods = data.claim.leave_details.continuous_leave_periods;
  if (period < continuousPeriods.length) {
    const leavePeriod = continuousPeriods[period];
    const absenceStatusSelect = await Util.labelled(browser, "Absence status");
    await browser.selectByText(absenceStatusSelect, "Estimated");

    const startDateInput = await Util.labelled(browser, "Absence start date");
    await browser.type(startDateInput, Util.formatDate(leavePeriod.start_date));
    const endDateInput = await Util.labelled(browser, "Absence end date");
    await browser.type(endDateInput, Util.formatDate(leavePeriod.end_date));
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

export default async (): Promise<void> => {
  TestData.fromJSON<Cfg.LSTSimClaim>(`../data/claims.json`).filter(
    (line) => line.scenario === scenario
  );

  steps.forEach((action) => {
    step(action.name, action.test as StepFunction<unknown>);
  });
};
