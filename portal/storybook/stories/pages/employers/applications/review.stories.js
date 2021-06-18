import Document, { DocumentType } from "src/models/Document";
import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import DocumentCollection from "src/models/DocumentCollection";
import { MockEmployerClaimBuilder } from "tests/test-utils";
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
        options: ["Bonding", "Medical", "Care"],
      },
    },
    // Todo(EMPLOYER-1453): remove V1 eform functionality
    "Claimant EForm Version": {
      defaultValue: "Version 1 (before 2021-07-14)",
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
          "Hours worked per week - invalid_hours_worked_per_week",
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

export const Default = (args) => {
  const { claimOption } = args;
  const errorTypes = args.errorTypes || [];

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
      claim: claim.create(),
      documents: getDocuments(documentationOption),
      downloadDocument: () => {},
      loadClaim: () => {},
      loadDocuments: () => {},
      submit: () => {},
    },
    setAppErrors: () => {},
  };

  return <Review appLogic={appLogic} query={query} user={user} />;
};

function getDocuments(documentation) {
  const isWithoutDocumentation = documentation.includes(
    "without documentation"
  );
  const documentData = {
    application_id: "mock-application-id",
    content_type: "application/pdf",
    created_at: "2020-01-02",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: 202020,
    name: "Your Document",
  };

  return isWithoutDocumentation
    ? new DocumentCollection()
    : new DocumentCollection([new Document(documentData)]);
}

function getAppErrorInfoCollection(errorTypes = []) {
  const errors = [];
  if (
    errorTypes.includes("Hours worked per week - invalid_hours_worked_per_week")
  ) {
    errors.push(
      new AppErrorInfo({
        message:
          "hours_worked_per_week must be greater than 0 and less than 168",
        type: "invalid_hours_worked_per_week",
        field: "hours_worked_per_week",
      })
    );
  }

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
