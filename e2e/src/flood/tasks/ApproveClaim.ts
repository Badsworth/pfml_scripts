import { Browser, Locator, By, ElementHandle, Key } from "@flood/element";
import * as Cfg from "../config";
import * as Util from "../helpers";
import Tasks from "./index";

let evidenceApproved = false;

export const steps: Cfg.StoredStep[] = [
  checkApprovalReadiness(false),
  {
    name: "Paid Benefits",
    test: async (browser: Browser): Promise<void> => {
      const adjudicateButton = await browser.maybeFindElement(
        By.css("input[type='submit'][value='Adjudicate']")
      );
      if (adjudicateButton) {
        await browser.click(adjudicateButton);
        await browser.waitForNavigation();
      }

      const paidBenefitsTab = await Util.waitForElement(
        browser,
        By.visibleText("Paid Benefits")
      );
      await browser.click(paidBenefitsTab);

      const currentAvgWeeklyAge = parseFloat(
        (
          await (
            await Util.waitForElement(
              browser,
              By.css("[id*='paidBenefitsListviewAverageWeeklyWage0']")
            )
          ).text()
        ).replace(",", "")
      );

      if (currentAvgWeeklyAge < 1200) {
        const editButton = await Util.waitForElement(
          browser,
          By.css("input[type='submit'][value='Edit']")
        );
        await editButton.click();

        const avgWeeklyWage = await Util.labelled(
          browser,
          "Average weekly wage"
        );
        await browser.clear(avgWeeklyWage);
        await browser.type(avgWeeklyWage, "1200");

        const benefitPeriodSelect = await Util.waitForElement(
          browser,
          By.css("select[id*='benefitWaitingPeriodBasis']")
        );
        await browser.selectByText(benefitPeriodSelect, "Days");

        const okButton = await Util.waitForElement(
          browser,
          By.css("input[type='submit'][value='OK']")
        );
        await browser.click(okButton);
      }
    },
  },
  {
    name: "Accept Leave Plan",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      let manageRequestTab = await Util.waitForElement(
        browser,
        By.visibleText("Manage Request")
      );
      await browser.click(manageRequestTab);
      // check if availability can still be approved
      const familyLeavePlanAvailability = await Util.waitForElement(
        browser,
        getFamilyLeavePlanProp("AvailabilityStatus")
      );
      const availabilityStatus = await familyLeavePlanAvailability.text();
      // when it is Pending Certification, then we can make it pass
      if (availabilityStatus === "Pending Certification") {
        const evidenceTab = await Util.waitForElement(
          browser,
          By.visibleText("Evidence")
        );
        await evidenceTab.click();
        await certifyEvidence.test(browser, data);
      }
      // go back and try to approve leave plan
      manageRequestTab = await Util.waitForElement(
        browser,
        By.visibleText("Manage Request")
      );
      await browser.click(manageRequestTab);
      // select the right leave plan
      await (
        await Util.waitForElement(browser, getFamilyLeavePlanProp())
      ).click();
      // try accepting the leave plan
      const acceptButton = await Util.waitForElement(
        browser,
        By.css("input[type='submit'][value='Accept']")
      );
      await browser.click(acceptButton);
      await browser.waitForNavigation();
      // exit adjudication
      const okButton = await Util.waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await browser.click(okButton);
    },
  },
  {
    name: "Finalize claim adjudication",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      // check if leave has been accepted
      const leavePlanStatus = await (
        await Util.waitForElement(
          browser,
          getFamilyLeavePlanProp("DecisionStatus")
        )
      ).text();

      // if leave plan has not been accepted, deny claim
      // something was missing, most likely Availability errors
      if (leavePlanStatus !== "Accepted" || !evidenceApproved) {
        await Tasks.Deny(browser, data);
        return;
      }

      const approveButton = await Util.waitForElement(
        browser,
        By.css("a[aria-label='Approve']")
      );
      await approveButton.click();

      await Util.waitForElement(browser, By.visibleText("Approved"));
    },
  },
];

export function checkApprovalReadiness(
  exitAdjudication = true
): Cfg.StoredStep {
  return {
    name: "Claim Approval Readiness Check",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      // we're looking for a specific plan
      // because "Limit" leave plans break this flow
      const evidenceStatus = await (
        await Util.waitForElement(
          browser,
          getFamilyLeavePlanProp("EvidenceStatus")
        )
      ).text();
      // if evidence has not been reviewed yet,
      // approve all evidence
      evidenceApproved = evidenceStatus.indexOf("Satisfied") === 0;
      if (!evidenceApproved) {
        const adjudicateButton = await Util.waitForElement(
          browser,
          By.css("input[type='submit'][value='Adjudicate']")
        );
        await browser.click(adjudicateButton);

        await approveEvidence().test(browser, data);
        await certifyEvidence.test(browser, data);

        if (exitAdjudication) {
          const okButton = await Util.waitForElement(
            browser,
            By.css("input[type='submit'][value='OK']")
          );
          await browser.click(okButton);
          await browser.waitForNavigation();
        }
      }
    },
  };
}

export const approveEvidence = (
  specificDoc?: Cfg.StandardDocumentType
): Cfg.StoredStep => ({
  name: "Evidence Review",
  test: async (browser: Browser): Promise<void> => {
    console.info("Approve - Evidence Review");
    const evidenceTab = await Util.waitForElement(
      browser,
      By.visibleText("Evidence")
    );
    await evidenceTab.click();
    // get the list of documents attached to this claim
    const documents = await browser.findElements(
      By.css("table[id*='evidenceResultListviewWidget'] tr")
    );
    // if we have no documents to review, do nothing
    if (documents.length === 0) return;
    if (specificDoc) {
      await approveDocumentEvidence(browser, specificDoc);
    } else {
      // approve pending documents
      for (let i = 0; i < documents.length; i++) {
        await approveDocumentEvidence(browser, i);
      }
      evidenceApproved = true;
    }
  },
});

export const approveDocumentEvidence = async (
  browser: Browser,
  doc: number | Cfg.StandardDocumentType
): Promise<boolean> => {
  // search for this documents' review decision
  let evidence: ElementHandle;

  if (typeof doc === "number") {
    evidence = await Util.waitForElement(
      browser,
      By.css(
        `table[id*='evidenceResultListviewWidget'] tr:nth-child(${
          doc + 1
        }) td:nth-child(5)`
      )
    );
  } else {
    evidence = await Util.waitForElement(
      browser,
      By.css(`td[title*="${doc}"] ~ td:nth-child(5)`)
    );
  }
  // if document decision is not pending, ignore
  if ((await evidence.text()) !== "Pending") return false;
  // confirmed it is pending, so we continue with approval
  await browser.doubleClick(evidence);

  await browser.wait(1000);
  const manageButton = await Util.waitForElement(
    browser,
    By.css("input[type='submit'][value='Manage Evidence']")
  );
  await manageButton.click();

  const receiptSelect = await Util.labelled(browser, "Evidence Receipt");
  await browser.selectByText(receiptSelect, "Received");

  const decisionSelect = await Util.labelled(browser, "Evidence Decision");
  await browser.selectByText(decisionSelect, "Satisfied");

  const reasonInput = await Util.labelled(browser, "Evidence Decision Reason");
  await browser.sendKeyCombinations(Key.SHIFT, Key.END);
  await browser.sendKeys(Key.BACK_SPACE);
  await browser.type(reasonInput, "PFML - Approved for LST purposes");

  const okButton = await Util.waitForElement(
    browser,
    By.css("table[id*='Popup'] input[type='button'][value='OK']")
  );
  await okButton.click();
  await browser.wait(1000);
  return true;
};

export const certifyEvidence: Cfg.StoredStep = {
  name: "Evidence Certification",
  test: async (browser: Browser): Promise<void> => {
    console.info("Approve - Evidence Certification");
    const certificationTab = await Util.waitForElement(
      browser,
      By.visibleText("Certification Periods")
    );
    await certificationTab.click();

    const prefillButton = await Util.waitForElement(
      browser,
      By.css(
        "input[type='submit'][value='Prefill with Requested Absence Periods']"
      )
    );
    await prefillButton.click();

    const yesButton = await Util.waitForElement(
      browser,
      By.css(".popup_buttons input[type='submit'][value='Yes']")
    );
    await yesButton.click();
    await browser.waitForNavigation();
  },
};

export default async (
  browser: Browser,
  data: Cfg.LSTSimClaim
): Promise<void> => {
  const isEligible = await Util.isFinanciallyEligible(browser);
  if (isEligible) {
    for (const step of steps) {
      const stepName = `Approve - ${step.name}`;
      try {
        console.info(stepName);
        await step.test(browser, data);
      } catch (e) {
        throw new Error(`Failed to execute step "${stepName}": ${e}`);
      }
    }
  } else {
    // Deny claim due to lack of Financial Eligibility
    console.info(
      "Tried to Approve but denied claim due to lack of Financial Eligibility"
    );
    await Tasks.Deny(browser, data);
  }
};

type FineosLeavePlanProps =
  | "DecisionStatus"
  | "EligibilityIcon"
  | "AvailabilityStatus"
  | "EvidenceIcon"
  | "EvidenceStatus";

export function getFamilyLeavePlanProp(
  type: FineosLeavePlanProps = "DecisionStatus"
): Locator {
  return By.js((planProp) => {
    const leavePlans = document.querySelectorAll("table[id*='leavePlan'] tr");
    let myLeavePlan = 0;
    Array.from(leavePlans).forEach((tr, i) => {
      if (tr.textContent?.toString().includes("MA PFML - Family")) {
        myLeavePlan = i;
        return false;
      }
    });
    myLeavePlan = myLeavePlan + 1;
    let propertyColumn = 1;
    if (planProp === "EligibilityIcon") {
      propertyColumn = 3;
    } else if (planProp === "EvidenceIcon") {
      propertyColumn = 5;
    } else if (planProp === "EvidenceStatus") {
      propertyColumn = 6;
    } else if (planProp === "AvailabilityStatus") {
      propertyColumn = 8;
    } else if (planProp === "DecisionStatus") {
      propertyColumn = 14;
    }
    const icon = document.querySelector(
      `tr:nth-child(${myLeavePlan}) td:nth-child(${propertyColumn})${
        planProp.includes("Icon") ? " i" : ""
      }`
    );
    return icon;
  }, type);
}
