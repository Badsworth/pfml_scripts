import { Page } from "playwright-chromium";
import { GeneratedClaim } from "../generation/Claim";
import { getDocumentReviewTaskName } from "../util/documents";
import { Claim, Fineos } from "./fineos.pages";

export function withFineosBrowser<T extends unknown>(
  next: (page: Page) => Promise<T>,
  debug = false,
  screenshots?: string
): Promise<T> {
  return Fineos.withBrowser(next, debug, screenshots);
}

export async function approveClaim(
  page: Page,
  claim: GeneratedClaim,
  fineos_absence_id: string
): Promise<void> {
  // Visit the claim
  const claimPage = await Claim.visit(page, fineos_absence_id);
  // Start adjudication
  await claimPage.adjudicate(async (adjudication) => {
    await adjudication.acceptLeavePlan();

    await adjudication.evidence(async (evidence) => {
      for (const { document_type } of claim.documents)
        await evidence.receive(document_type);
    });

    await adjudication.certificationPeriods(async (certification) => {
      await certification.prefill();
    });
  });
  await claimPage.tasks(async (tasks) => {
    // Close document tasks
    for (const document of claim.documents)
      await tasks.close(getDocumentReviewTaskName(document.document_type));
    // Close ER approval task
    await tasks.close("Employer Approval Received");
  });
  await claimPage.approve();
}

export async function denyClaim(
  page: Page,
  fineos_absence_id: string
): Promise<void> {
  const claimPage = await Claim.visit(page, fineos_absence_id);
  // go into adjudication
  await claimPage.adjudicate(async (adjudication) => {
    // deny leave plan
    await adjudication.denyLeavePlan();
  });
  await claimPage.deny();
}

export async function closeDocuments(
  page: Page,
  claim: GeneratedClaim,
  fineos_absence_id: string
): Promise<void> {
  const claimPage = await Claim.visit(page, fineos_absence_id);
  await claimPage.adjudicate(async (adjudication) => {
    await adjudication.evidence(async (evidence) => {
      for (const { document_type } of claim.documents)
        await evidence.receive(document_type);
    });

    await adjudication.certificationPeriods((cert) => cert.prefill());
  });

  // Close all of the documentation review tasks.
  await claimPage.tasks(async (tasks) => {
    for (const { document_type } of claim.documents) {
      await tasks.close(getDocumentReviewTaskName(document_type));
    }

    if (claim.employerResponse?.has_amendments) {
      await tasks.close("Employer Conflict Reported");
      if (claim.employerResponse.concurrent_leave)
        await tasks.open("Escalate employer reported accrued paid leave (PTO)");
      if (claim.employerResponse.previous_leaves.length)
        await tasks.open("Escalate employer reported past leave");
      if (claim.employerResponse.employer_benefits.length)
        await tasks.open("Escalate Employer Reported Other Income");
    } else if (claim.employerResponse?.employer_decision === "Approve") {
      await tasks.close("Employer Approval Received");
    }
  });
}
