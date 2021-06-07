import { Browser, By, ElementHandle, Until } from "@flood/element";
import { byContains, byLabelled } from "../helpers";
import delay from "delay";

/**
 * Helper to switch to a particular tab.
 */
export async function onTab(browser: Browser, label: string): Promise<void> {
  await browser.click(byContains(".TabStrip td", label));
  await browser.wait(
    Until.elementLocated(byContains(".TabStrip td.TabOn", label))
  );
  await delay(100);
}

type StatusCategory =
  | "ApplicabilityStatus"
  | "EligibilityStatus"
  | "EvidenceStatus"
  | "AvailabilityStatus"
  | "RestrictionStatus"
  | "ProtocolsStatus"
  | "PlanDecision";
function getClaimStatus(
  browser: Browser,
  category: StatusCategory
): Promise<string> {
  const selector = `.divListviewGrid .ListTable td[id*='ListviewWidget${category}0']`;

  return browser.findElement(selector).then((el) => el?.text());
}

export class Claim {
  static async visit(browser: Browser, claimId: string): Promise<Claim> {
    await browser.click("a[aria-label='Cases']");
    await onTab(browser, "Case");
    await browser.type(byLabelled("Case Number"), claimId);
    await browser.type(byLabelled("Case Type"), "Absence Case");
    await browser.click(By.css("input[type='submit'][value='Search']"));
    await browser.waitForNavigation();

    return new Claim(browser);
  }
  constructor(private browser: Browser) {}

  async isApprovable(): Promise<boolean> {
    await this.browser.wait(
      Until.elementLocated("table[id*='leavePlanAdjudicationListviewWidget']")
    );
    const asrt = (
      category: StatusCategory,
      expected: string
    ): Promise<boolean> =>
      getClaimStatus(this.browser, category).then((val) => val === expected);
    return (
      (await asrt("ApplicabilityStatus", "Applicable")) &&
      (await asrt("EvidenceStatus", "Satisfied")) &&
      (await asrt("EligibilityStatus", "Met")) &&
      (await asrt("AvailabilityStatus", "Time Available")) &&
      (await asrt("RestrictionStatus", "Passed")) &&
      (await asrt("PlanDecision", "Accepted"))
    );
  }

  async approve(): Promise<void> {
    await this.browser.click('a[title="Approve the Pending Leaving Request"]');
    await this.browser.waitForNavigation();
    if ((await this.getClaimStatus()) !== "Approved") {
      throw new Error("Claim could not be approved");
    }
  }
  async deny(): Promise<void> {
    await this.browser.click('a[title="Deny the Pending Leave Request"]');
    await this.browser.wait(
      Until.elementLocated("#leaveRequestDenialDetailsWidget")
    );
    await this.browser.selectByText(
      byLabelled("Denial Reason"),
      "Non-eligible employee"
    );
    await this.browser.click("input[type='submit'][value='OK']");
    await this.browser.waitForNavigation();

    if ((await this.getClaimStatus()) !== "Declined") {
      throw new Error("Claim could not be denied");
    }
  }

  async adjudicate(cb: (page: AdjudicationPage) => unknown): Promise<void> {
    await this.browser.click('input[type="submit"][value="Adjudicate"]');
    await this.browser.waitForNavigation();
    await cb(new AdjudicationPage(this.browser));
    await this.browser.click("#footerButtonsBar input[value='OK']");
    await this.browser.waitForNavigation();
  }
  async getClaimStatus(): Promise<string> {
    return this.browser
      .findElement(".key-info-bar .status dd")
      .then((el) => el.text());
  }
}

class AdjudicationPage {
  constructor(private browser: Browser) {}
  async evidence(cb: (page: EvidencePage) => unknown): Promise<void> {
    await onTab(this.browser, "Evidence");
    await cb(new EvidencePage(this.browser));
  }
  async certificationPeriods(
    cb: (page: CertificationPage) => unknown
  ): Promise<void> {
    await onTab(this.browser, "Evidence");
    await onTab(this.browser, "Certification Periods");
    await cb(new CertificationPage(this.browser));
  }
  async maybeApprove() {
    await onTab(this.browser, "Manage Request");
    await this.browser.wait(
      Until.elementLocated(By.visibleText("Selected Leave Plan(s)"))
    );
    const getNextUndecidedPlan = async () => {
      await this.browser.wait(
        Until.elementLocated(
          "table[id*='selectedLeavePlansForLeaveRequestListviewWidget']"
        )
      );
      const rows = await this.browser.findElements(
        "table[id*='selectedLeavePlansForLeaveRequestListviewWidget'] tr"
      );
      for (const row of rows) {
        const decision = await row
          .findElement("td:nth-child(15)")
          .then((el) => el?.text());
        if (decision === "Undecided") {
          return row;
        }
      }
    };

    let limiter = 0;
    let planRow: ElementHandle | undefined;
    while ((planRow = await getNextUndecidedPlan()) && limiter++ < 3) {
      console.log("Starting to process plan row");
      const asrt = (index: number, expected: string) => {
        if (!planRow) throw new Error("This plan is malformed");
        return planRow
          .findElement(`td:nth-child(${index})`)
          .then(async (el) => (await el?.text()) === expected);
      };
      const planIsApprovable =
        (await asrt(3, "Applicable")) &&
        (await asrt(5, "Met")) &&
        (await asrt(7, "Satisfied")) &&
        (await asrt(9, "Met"));
      await planRow.click();
      const approve = await this.browser.maybeFindElement(
        'input[type="submit"][title="Accept Leave Plan"]'
      );
      const reject = await this.browser.maybeFindElement(
        'input[type="submit"][title="Reject Leave Plan"]'
      );

      if (planIsApprovable && approve && (await approve.isEnabled())) {
        console.log("Approving plan");
        await approve.click();
        await this.browser.waitForNavigation();
      } else if (reject && (await reject.isEnabled())) {
        console.log("Denying plan");
        await reject.click();
        await this.browser.waitForNavigation();
      }
    }
  }
}

class EvidencePage {
  constructor(private browser: Browser) {}

  private async getUnapprovedEvidence(): Promise<ElementHandle | undefined> {
    await this.browser.wait(
      Until.elementLocated("table[id*='evidenceResultListviewWidget'] tr")
    );
    const evidenceRows = await this.browser.findElements(
      "table[id*='evidenceResultListviewWidget'] tr"
    );

    for (const row of evidenceRows) {
      const statusElement = await row.findElement("td:nth-child(5)");
      const name = await row.text();
      const statusText = await statusElement?.text();
      console.log("Status text is", statusText, name);
      if (statusText !== "Satisfied") {
        return row;
      }
    }
  }

  async approveAll() {
    let activeDocument: ElementHandle | undefined;
    while ((activeDocument = await this.getUnapprovedEvidence())) {
      await activeDocument.click();
      await this.browser.click('input[type="submit"][value="Manage Evidence"]');
      await this.browser.selectByText(
        byLabelled("Evidence Receipt"),
        "Received"
      );
      await this.browser.selectByText(
        byLabelled("Evidence Decision"),
        "Satisfied"
      );
      // @todo: Clear the contents of the field first.
      await this.browser.type(
        byLabelled("Evidence Decision Reason"),
        "Evidence has been received by LST bot."
      );
      await this.browser.click(
        ".WidgetPanelEditPopup input[type='button'][value='OK']"
      );
      await this.browser.wait(1000);
    }
  }
}

class CertificationPage {
  constructor(private browser: Browser) {}
  async maybePrefill() {
    await this.browser.wait(
      Until.elementLocated(
        By.visibleText("Certified Episodic Leave Entitlement")
      )
    );
    const button = await this.browser.maybeFindElement(
      "input[value='Prefill with Requested Absence Periods']"
    );
    if (button && (await button.isEnabled())) {
      await button.click();
      await this.browser.click("#PopupContainer input[value='Yes']");
      await this.browser.waitForNavigation();
    }
  }
}
