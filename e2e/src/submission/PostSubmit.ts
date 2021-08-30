import { Page } from "playwright-chromium";
import { GeneratedClaim } from "../generation/Claim";
import { getDocumentReviewTaskName } from "../util/documents";
import { Claim } from "./fineos.pages";
import winston from "winston";

export async function approveClaim(
  page: Page,
  claim: GeneratedClaim,
  fineos_absence_id: string,
  logger?: winston.Logger
): Promise<void> {
  // Visit the claim
  const claimPage = await Claim.visit(page, fineos_absence_id);
  // Start adjudication
  logger?.debug("Starting Adjudication Process in Fineos", {
    fineos_absence_id,
  });
  await claimPage.adjudicate(async (adjudication) => {
    await adjudication.acceptLeavePlan();
    logger?.debug("Accept Leave Plan complete", {
      fineos_absence_id,
    });
    await adjudication.evidence(async (evidence) => {
      for (const { document_type } of claim.documents)
        await evidence.receive(document_type);
    });
    logger?.debug("Evidence has been recieved", {
      fineos_absence_id,
    });
    await adjudication.certificationPeriods(async (certification) => {
      await certification.prefill();
    });
    logger?.debug("Certification Periods have been pre-filled", {
      fineos_absence_id,
    });
  });
  logger?.debug("Adjudication Completed w/o errors:", {
    fineos_absence_id,
  });
  logger?.debug("Attempting to close Tasks ...", {
    fineos_absence_id,
  });
  await claimPage.tasks(async (tasks) => {
    // Close document tasks
    for (const document of claim.documents)
      await tasks.close(getDocumentReviewTaskName(document.document_type));
    // Close ER approval task
    await tasks.close("Employer Approval Received");
  });
  logger?.debug("Document & ER approval task have been closed", {
    fineos_absence_id,
  });
  logger?.debug("Attempting to approve claim ...", {
    fineos_absence_id,
  });
  await claimPage.approve();
  logger?.debug("Claim was approved in Fineos", {
    fineos_absence_id,
  });
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
