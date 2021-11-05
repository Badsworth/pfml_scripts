import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import DocumentCollection from "src/models/DocumentCollection";
import { DocumentType } from "src/models/Document";
import { MockEmployerClaimBuilder } from "tests/test-utils";
import { Props } from "storybook/types";
import React from "react";
import { Review } from "src/pages/employers/applications/review";
import User from "src/models/User";

export default {
  title: "Pages/Employers/Applications/Review",
  component: Review,
  argTypes: {
    claimOption: {
      defaultValue: "Continuous or reduced - documentation",
      control: {
        type: "radio",
        options: [
          "Continuous or reduced - documentation",
          "Continuous or reduced - without documentation",
          "Intermittent - documentation",
          "Intermittent - without documentation",
        ],
      },
    },
    "Leave reason": {
      defaultValue: "Medical",
      control: {
        type: "radio",
        options: ["Bonding", "Medical", "Care", "Pregnancy"],
      },
    },
    // Todo(EMPLOYER-1453): remove V1 eform functionality
    "Claimant EForm Version": {
      defaultValue: "Version 2 (after 2021-07-14)",
      control: {
        type: "radio",
        options: [
          "Version 1 (before 2021-07-14)",
          "Version 2 (after 2021-07-14)",
        ],
      },
    },
    errorTypes: {
      control: {
        type: "check",
        options: [
          "Hours worked per week - minimum",
          "Hours worked per week - maximum",
          "Employer benefit - benefit end date",
          "Previous leave - leave start date",
          "Previous leave - leave end date",
        ],
      },
    },
  },
};

export const Default = (
  args: Props<typeof Review> & {
    claimOption: string;
    "Claimant EForm Version": string;
    errorTypes: string[];
    "Leave reason": string;
  }
) => {
  const { claimOption } = args;
  const errorTypes = args.errorTypes || [];

  // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
  const user = new User();
  const query = { absence_id: "mock-absence-id" };
  const leavePeriodType = claimOption.split("-")[0];
  const documentationOption = claimOption.split("-")[1];
  const isIntermittent = !!leavePeriodType.includes("Intermittent");

  let claim = new MockEmployerClaimBuilder()
    .completed(isIntermittent)
    .previousLeaves()
    .reviewable();

  switch (args["Leave reason"]) {
    case "Bonding":
      claim = claim.bondingLeaveReason();
      break;
    case "Medical":
      claim = claim.medicalLeaveReason();
      break;
    case "Care":
      claim = claim.caringLeaveReason();
      break;
    case "Pregnancy":
      claim = claim.pregnancyLeaveReason();
      break;
  }

  switch (args["Claimant EForm Version"]) {
    case "Version 1 (before 2021-07-14)":
      claim = claim.eformsV1();
      break;
    case "Version 2 (after 2021-07-14)":
      claim = claim.eformsV2().concurrentLeave();
      break;
  }

  const appLogic = {
    appErrors: getAppErrorInfoCollection(errorTypes),
    employers: {
      claimDocumentsMap: getDocumentsMap(
        documentationOption,
        claim.create().leave_details.reason
      ),
      downloadDocument: () => {},
      loadClaim: () => {},
      loadDocuments: () => {},
      submit: () => {},
    },
    setAppErrors: () => {},
  };

  return (
    <Review
      // @ts-expect-error ts-migrate(2740) FIXME: Type '{ appErrors: AppErrorInfoCollection; employe... Remove this comment to see the full error message
      appLogic={appLogic}
      query={query}
      user={user}
      claim={claim.create()}
    />
  );
};

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'documentation' implicitly has an 'any' ... Remove this comment to see the full error message
function getDocumentsMap(documentation, leaveReason) {
  const isWithoutDocumentation = documentation.includes(
    "without documentation"
  );
  const documentData = {
    application_id: "mock-application-id",
    content_type: "application/pdf",
    created_at: "2020-01-02",
    // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    document_type: DocumentType.certification[leaveReason],
    fineos_document_id: 202020,
    name: `${leaveReason} document`,
  };

  return isWithoutDocumentation
    ? new Map([["mock-absence-id", new DocumentCollection()]])
    : // @ts-expect-error ts-migrate(2322) FIXME: Type '{ application_id: string; content_type: stri... Remove this comment to see the full error message
      new Map([["mock-absence-id", new DocumentCollection([documentData])]]);
}

function getAppErrorInfoCollection(errorTypes: string[] = []) {
  const errors = [];

  if (errorTypes.includes("Hours worked per week - minimum")) {
    errors.push(
      new AppErrorInfo({
        message: "Enter the average weekly hours.",
        type: "minimum",
        field: "hours_worked_per_week",
      })
    );
  }

  if (errorTypes.includes("Hours worked per week - maximum")) {
    errors.push(
      new AppErrorInfo({
        message: "Average weekly hours must be 168 or fewer.",
        type: "maximum",
        field: "hours_worked_per_week",
      })
    );
  }

  if (errorTypes.includes("Employer benefit - benefit end date")) {
    errors.push(
      new AppErrorInfo({
        message: "benefit_end_date cannot be earlier than benefit_start_date",
        type: "minimum",
        field: "employer_benefits[0].benefit_end_date",
      })
    );
  }

  if (errorTypes.includes("Previous leave - leave start date")) {
    errors.push(
      new AppErrorInfo({
        message: "Previous leaves cannot start before 2021",
        type: "invalid_previous_leave_start_date",
        field: "previous_leaves[0].leave_start_date",
      })
    );
  }

  if (errorTypes.includes("Previous leave - leave end date")) {
    errors.push(
      new AppErrorInfo({
        message: "leave_end_date cannot be earlier than leave_start_date",
        type: "minimum",
        field: "previous_leaves[0].leave_end_date",
      })
    );
  }

  return new AppErrorInfoCollection(errors);
}
