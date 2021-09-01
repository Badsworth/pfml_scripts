import { DocumentUploadRequest } from "_api";
import { format, addMonths, addDays } from "date-fns";
import { config, getFineosBaseUrl } from "./common";
import { Credentials } from "../../src/types";
/**
 * This function is used to fetch and set the proper cookies for access Fineos UAT
 *
 * Note: Only used for UAT enviornment
 */
function SSO(credentials?: Credentials): void {
  cy.clearCookies();
  // Perform SSO login in a task. We can't visit other domains in Cypress.
  cy.task("completeSSOLoginFineos", credentials).then((cookiesJson) => {
    const deserializedCookies: Record<string, string>[] =
      JSON.parse(cookiesJson);
    // Filter out any cookies that will fail to be set. Those are ones where secure: false
    // and sameSite: "None"
    const noSecure = deserializedCookies.filter(
      (cookie) => !(!cookie.secure && cookie.sameSite === "None")
    );
    for (const cookie_info of noSecure) {
      cy.setCookie(cookie_info.name, cookie_info.value, cookie_info);
    }
  });
}

/**
 * Sets up Cypress to work with fineos. This includes:
 * 1. Intercepting known errors and error pages.
 * 2. Handling authentication and SSO Login.
 * 3. Setting the baseURL
 * 4. Navigating to fineos home page.
 * @param credentials you can override the credentials used for authenticating to fineos,
 * an example use case would be testing secure actions in `uat` environment,
 * where we need to use 2 different fineos accounts.
 * @example
 * fineos.before() // set's up fineos with default credentials.
 * fineos.before({username:config('SSO2_USERNAME'), password: config('SSO2_PASSWORD')})
 * // set's up login for the second SSO account
 */
export function before(credentials?: Credentials): void {
  Cypress.config(
    "baseUrl",
    getFineosBaseUrl(credentials?.username, credentials?.password)
  );
  // Fineos error pages have been found to cause test crashes when rendered. This is very hard to debug, as Cypress
  // crashes with no warning and removes the entire run history, so when a Fineos error page is detected, we replace the
  // page with an error page and capture the real response to a file for future debugging.
  cy.intercept(/\/(util\/errorpage\.jsp|outofdatedataerror\.jsp)/, (req) => {
    req.continue((res) => {
      // const filename = Math.ceil(Math.random() * 1000).toString() + `.json`;
      // We can't use Cypress's normal async methods here. Instead, use cy.now() to skip the command queue.
      // This is very undocumented and very not recommended, but I can't find a cleaner way to capture this data to disk
      // before we return the fake response.
      // @ts-ignore
      // cy.now(
      //   "writeFile",
      //   `cypress/screenshots/${filename}`,
      //   JSON.stringify({
      //     url: req.url,
      //     headers: res.headers,
      //     body: res.body,
      //   })
      // );

      // We need to extract this obstructive logic included in a FINEOS error page and replace it with a setTimeout to throw an error letting us know this page was encountered
      // Using the "modifyObstuctiveCode" property in the cypress.json was enough to get the error page to display but it was not enough to mitigate the test from hanging.
      // This approach behaves in a much more predictable manner (Error thrown)
      const body: string = res.body.replace(
        "if (top != self) { top.location=self.location }",
        "window.setTimeout(function _() { throw new Error('A FINEOS error page was detected during this test. An error is being thrown in order to prevent Cypress from crashing.') }, 500)\n"
      );
      res.send(body);
    });
  });

  // Set up a route we can listen to wait on ajax rendering to complete.
  cy.intercept(
    /(ajax\/pagerender\.jsp|sharedpages\/ajax\/listviewpagerender\.jsp|AJAXRequestHandler\.do)/
  ).as("ajaxRender");

  if (config("ENVIRONMENT") === "uat") {
    SSO();
  }
  cy.visit("/");
}

export function visitClaim(claimId: string): void {
  cy.get('a[aria-label="Cases"]').click();
  onTab("Case");
  cy.findByLabelText("Case Number").type(claimId);
  cy.findByLabelText("Case Type").select("Absence Case");
  cy.get('input[type="submit"][value="Search"]').click();
  assertAbsenceCaseNumber(claimId);
}

/**
 * Called from the claim page, asserts that the claim status is an expected value.
 */
export function assertClaimStatus(expected: string): void {
  cy.get(".key-info-bar .status dd").should((statusElement) => {
    expect(statusElement, `Absence case should be ${expected}`).to.contain.text(
      expected
    );
  });
}

export function assertHasDocument(name: string): void {
  cy.get("table[id*='DocumentsForCaseListviewWidget']").should((table) => {
    expect(table, `Expected to find a "${name}" document`).to.have.descendants(
      `a:contains("${name}")`
    );
  });
}

/**
 * Called from the claim page, asserts Absence Case is the expected value.
 */
export function assertAbsenceCaseNumber(claimNumber: string): void {
  cy.get(".case_pageheader_title").should((statusElement) => {
    expect(
      statusElement,
      `Absence Case ID should be: ${claimNumber}`
    ).to.contain.text(claimNumber);
  });
}

/**
 * Helper to switch to a particular tab.
 */
export function onTab(label: string): void {
  cy.contains(".TabStrip td", label).then((tab) => {
    if (tab.hasClass("TabOn")) {
      return; // We're already on the correct tab.
    }
    // Here we are splitting the action and assertion, because the tab class can be added after a re-render.
    cy.contains(".TabStrip td", label).click({ force: true });
    waitForAjaxComplete();
    cy.contains(".TabStrip td", label).should("have.class", "TabOn");
  });
}

/**
 * Helper to wait for ajax-y actions to complete before proceeding.
 *
 * Note: Please do not add explicit waits here. This function should be fast -
 * it will be called often. Try to find a better way to determine if we can move
 * on with processing (element detection).
 */
export function wait(): void {
  cy.wait("@ajaxRender");
  // The complicated cy.root().closest('html')... command makes sure this function can be used inside the cy.within() context
  cy.root()
    .should(($el) => {
      expect(Cypress.dom.isAttached($el)).to.be.true;
    })
    .closest(`html`)
    .should(($el) => {
      expect(Cypress.dom.isAttached($el)).to.be.true;
    })
    .find(`#disablingLayer`)
    .should(($el) => {
      expect(Cypress.dom.isAttached($el)).to.be.true;
    })
    .should("not.be.visible");
}

export function waitForAjaxComplete(): void {
  cy.window({ timeout: 30000 })
    .invoke("axGetAjaxQueueManager")
    .should((q) => {
      const inFlight = Object.values(q.requests).filter(
        // @ts-ignore - ignore uses of Fineos internal window properties.
        (req) => req.state() !== "resolved"
      );
      expect(inFlight, "In-flight Ajax requests should be 0").to.have.length(0);
    });
}

export function clickBottomWidgetButton(value = "OK"): void {
  cy.get(`#PageFooterWidget input[value="${value}"]`).click({ force: true });
}

export function addBondingLeaveFlow(timeStamp: Date): void {
  cy.get('a[aria-label="Add Time"]').click({ force: true });
  cy.get('input[type="radio"][value*="another_reason_id"]').click();
  cy.get('input[type="submit"][title="Add Time Off Period"]').click();
  cy.wait("@ajaxRender");
  cy.wait(200);
  cy.get(".popup-container").within(() => {
    cy.findByLabelText("Absence status").select("Known");
    cy.wait("@ajaxRender");
    cy.wait(200);
    const startDate = addMonths(timeStamp, 2);
    const startDateFormatted = format(startDate, "MM/dd/yyyy");
    const endDateFormatted = format(addDays(startDate, 2), "MM/dd/yyyy");

    cy.findByLabelText("Absence start date").type(
      `{selectall}{backspace}${startDateFormatted}{enter}`
    );
    cy.wait("@ajaxRender");
    cy.wait(200);
    cy.findByLabelText("Absence end date").type(
      `{selectall}{backspace}${endDateFormatted}{enter}`
    );
    cy.wait("@ajaxRender");
    cy.wait(200);
    cy.get("input[type='checkbox'][id*='startDateAllDay_CHECKBOX']").click();
    cy.get("input[type='checkbox'][id*='endDateAllDay_CHECKBOX']").click();
    cy.get("input[type='submit'][value='OK']").click();
  });
  clickBottomWidgetButton("Next");
  cy.wait("@ajaxRender");
  cy.wait(200);
  // Work Pattern
  cy.get("input[type='checkbox'][id*='standardWorkWeek_CHECKBOX']").click();
  cy.findByLabelText("Pattern Status").select("Known");
  clickBottomWidgetButton("Next");
  cy.wait("@ajaxRender");
  cy.wait(200);
  // Complete Details
  cy.findByLabelText("Primary Relationship to Employee").select("Child");
  cy.wait("@ajaxRender");
  cy.wait(200);
  cy.wait("@ajaxRender");
  cy.wait(200);
  cy.findByLabelText("Qualifier 1").select("Biological");
  clickBottomWidgetButton("Next");
  // Additional Info
  clickBottomWidgetButton("Next");
  // Wrap up
  clickBottomWidgetButton("OK");
  // Assert bonding leave request was added
  cy.get("[id*='processPhaseEnum']").should("contain.text", "Adjudication");
  cy.get("[id*='requestedLeaveCardWidget']").should(
    "contain.text",
    "Pending leave"
  );
  cy.get(".absencePeriodDescription").should(
    "contain.text",
    "Fixed time off for Child Bonding"
  );
  cy.wait(1000);
}

export function findOtherLeaveEForm(claimNumber: string): void {
  visitClaim(claimNumber);
  onTab("Documents");
  assertHasDocument("Other Leaves");
  cy.wait(200);
}

/**Clicks on the 'Next' or 'Previous' button to move to the next/previous step during the intake process or recording actual leave */
export const clickNext = (
  buttonName: "Next" | "Previous" = "Next"
): Cypress.Chainable<JQuery<HTMLElement>> =>
  cy
    .get(`#nextPreviousButtons input[value*='${buttonName} ']`)
    .click({ force: true });
/**
 * Takes document type and returns fixture file name.
 * @param document_type document type as specified in the `claim.documents`
 * @returns name of the fixture file, see `e2e/cypress/fixtures`
 */
export function getFixtureDocumentName(
  document_type: DocumentUploadRequest["document_type"]
): string {
  switch (document_type) {
    case "Driver's License Mass":
    case "Identification Proof":
    case "Passport":
      return "MA_ID" as const;
    case "Driver's License Other State":
      return "OOS_ID" as const;
    case "Own serious health condition form":
      return "HCP" as const;
    case "Child bonding evidence form":
      return "FOSTER" as const;
    case "Certification Form":
      return "ADOPTION" as const;

    default:
      return "HCP" as const;
  }
}

/**
 * Asserts there's an error message displayed which matches a given text.
 * @param message text of the message
 * @example
 * fineos.assertErrorMessage("Hours worked per week must be entered");
 */
export function assertErrorMessage(message: string): void {
  cy.get(`#page_messages_container`).should("contain.text", message);
}

/**
 * Selects the folder at the end of the path, opening subfolders along the way as needed.
 * @param path path leading to the folder
 * @example
 * selectFolder(["State of Mass", "eForms"])
 */
export function selectFolder(path: string[]): void {
  const log = Cypress.log({
    displayName: "SELECT FOLDER",
    message: [`Opening path: ${JSON.stringify(path)}`],
    // @ts-ignore
    autoEnd: false,
  });
  log.snapshot("before");
  // Set a helper, since we need to reselect the whole tree widget often.
  const withinTree = (
    cb: () => unknown
  ): Cypress.Chainable<JQuery<HTMLElement>> =>
    cy
      .get(`#DocTypeFolderTreeviewWidget .TreeRootContainer`, { log: false })
      .within(cb);

  path.forEach((subfolder, i) => {
    if (i === path.length - 1) {
      withinTree(() =>
        cy.contains("#nodeElement", subfolder, { log: false }).then((el) => {
          if (el.parent().hasClass("TreeNodeSelected")) return;
          cy.wrap(el, { log: false }).click({ log: false });
          waitForAjaxComplete();
        })
      );
      withinTree(() => {
        cy.contains("#nodeElement", subfolder, { log: false })
          .parent({ log: false })
          .should("have.class", "TreeNodeSelected", { log: false });
      });
      return;
    }
    withinTree(() =>
      // Click on the handle to expand the subfolder.
      cy
        .contains("div.TreeNodeContainer", subfolder, { log: false })
        .find(`#nodeHandle`, { log: false })
        .then((el) => {
          if (el.hasClass("TreeNodeHandleExpanded")) return;
          cy.wrap(el, { log: false }).click({ log: false });
          waitForAjaxComplete();
        })
    );
    withinTree(() =>
      cy
        .contains("div.TreeNodeContainer", subfolder, { log: false })
        .find(`#nodeHandle`, { log: false })
        .should("have.class", "TreeNodeHandleExpanded", { log: false })
    );
  });
  log.snapshot("after");
  log.end();
}

/**
 * Opens the folder at the end of a given path, checks if contains given document(s)
 * @param documentName a string or an array of strings describing documents you expect to find.
 * @param path path to folder containing the documents as an array of strings.
 * @example
 * const certificationDocuments = ["Own serious health condition form", "Pregnancy/Maternity form"]
 * assertDocumentsInFolder(certificationDocuments, ["State of Mass", "Inbound Documents"]);
 * //Opens folder located at root/"State of Mass"/"Inbound Documents"
 */
export function assertDocumentsInFolder(
  documentName: string | string[],
  path: string[]
): void {
  selectFolder(path);
  if (Array.isArray(documentName))
    return documentName.forEach((name) =>
      cy.get("#DocumentTypeListviewWidget").should("contain.text", name)
    );
  cy.get("#DocumentTypeListviewWidget").should("contain.text", documentName);
}

/**
 * Returns claim adjudication status wrapped in Cypress.Chainable.
 * @returns Adjudication status of the claim
 * @example
 * fineos.getClaimStatus().then((status) => {
 *  if (status === "Approved"){
 *    //...your code here
 *  }
 * }
 */
export function getClaimStatus(): Cypress.Chainable<
  "Adjudication" | "Approved" | "Declined" | "Closed" | "In Review"
> {
  return cy.get(".key-info-bar .status dd").invoke("text");
}
