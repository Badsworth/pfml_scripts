import {
  approveClaim,
  assertHasTask,
  clickBottomWidgetButton,
  denyClaim,
  markEvidence,
  onTab,
  triggerNoticeRelease,
  visitClaim,
} from "./fineos";

type StatusCategory =
  | "Applicability"
  | "Eligibility"
  | "Evidence"
  | "Availability"
  | "Restriction"
  | "Protocols"
  | "PlanDecision";

/**
 * This is a page object for interacting with Fineos.
 *
 * It abstracts the concrete details of how an action is performed, and presents a descriptive API that allows the
 * test to describe _what_ needs to be done.
 *
 * There are two main constructs used in this API:
 *   * Enclosed callbacks (eg: adjudicate()), where an action is being performed within a given scope, and that scope
 *       only exists for a short period of time and should be "closed" immediately after.
 *   * Assertions/actions, (eg: assertStatus() or approve()), which are performed on the current page.
 *
 * To keep things DRY, both enclosed callbacks and assertions/actions should return the page object itself, allowing
 * calls to be chained together.
 */
export class ClaimPage {
  static visit(id: string): ClaimPage {
    visitClaim(id);
    return new ClaimPage();
  }

  adjudicate(cb: (page: AdjudicationPage) => unknown): this {
    cy.get('input[type="submit"][value="Adjudicate"]').click();
    cb(new AdjudicationPage());
    cy.get("#footerButtonsBar input[value='OK']").click();
    return this;
  }
  tasks(cb: (page: TasksPage) => unknown): this {
    onTab("Tasks");
    cb(new TasksPage());
    onTab("Absence Hub");
    return this;
  }
  shouldHaveStatus(category: StatusCategory, expected: string): this {
    const selector =
      category === "PlanDecision"
        ? `.divListviewGrid .ListTable td[id*='ListviewWidget${category}0']`
        : `.divListviewGrid .ListTable td[id*='ListviewWidget${category}Status0']`;
    cy.get(selector).should((element) => {
      expect(
        element,
        `Expected claim's "${category}" to be "${expected}"`
      ).to.have.text(expected);
    });
    return this;
  }
  triggerNotice(type: string): this {
    triggerNoticeRelease(type);
    return this;
  }
  approve(): this {
    approveClaim();
    return this;
  }
  deny(reason: string): this {
    denyClaim(reason);
    return this;
  }
}

class AdjudicationPage {
  private activeTab: string;

  constructor() {
    this.activeTab = "Manage Request";
  }

  private onTab(...path: string[]) {
    if (this.activeTab !== path.join(",")) {
      for (const part of path) {
        onTab(part);
      }
      this.activeTab = path.join(",");
    }
  }
  evidence(cb: (page: EvidencePage) => unknown): this {
    this.onTab("Evidence");
    cb(new EvidencePage());
    return this;
  }
  certificationPeriods(cb: (page: CertificationPeriodsPage) => unknown): this {
    this.onTab("Evidence", "Certification Periods");
    cb(new CertificationPeriodsPage());
    return this;
  }
  acceptLeavePlan() {
    this.onTab("Manage Request");
    cy.wait(50);
    cy.get("input[type='submit'][value='Accept']").click();
  }
}

class EvidencePage {
  receive(...args: Parameters<typeof markEvidence>): this {
    markEvidence(...args);
    return this;
  }
  requestAdditionalInformation(
    documentType: string,
    incomplete: Record<string, string>,
    comment: string
  ): this {
    cy.contains(".ListTable td", documentType).click();
    cy.get("input[type='submit'][value='Additional Information']").click();
    for (const [part, message] of Object.entries(incomplete)) {
      cy.contains("#AddExtraDataWidget tr", part).within(() => {
        cy.root().find("input[type='checkbox']").click();
        cy.root().find("input[type='text']").type(message);
      });
    }
    cy.get("textarea[name*='missingInformationBox']").type(comment);
    clickBottomWidgetButton("OK");
    cy.wait("@ajaxRender");
    cy.wait(200);
    return this;
  }
}
class CertificationPeriodsPage {
  prefill() {
    cy.get("input[value='Prefill with Requested Absence Periods']").click();
    cy.get("#PopupContainer input[value='Yes']").click();
    return this;
  }
}
class TasksPage {
  assertTaskExists(name: string): this {
    assertHasTask(name);
    return this;
  }
}
