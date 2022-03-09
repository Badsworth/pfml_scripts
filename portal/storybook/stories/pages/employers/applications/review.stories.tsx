import { ClaimDocument, DocumentType } from "src/models/Document";
import LeaveReason, { LeaveReasonType } from "src/models/LeaveReason";
import { AbsencePeriod } from "src/models/AbsencePeriod";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import EmployerClaim from "src/models/EmployerClaim";
import { ManagedRequirement } from "src/models/ManagedRequirement";
import { MockEmployerClaimBuilder } from "lib/mock-helpers/mock-model-builder";
import { Props } from "types/common";
import React from "react";
import { Review } from "src/pages/employers/applications/review";
import User from "src/models/User";
import { ValidationError } from "src/errors";
import createAbsencePeriod from "lib/mock-helpers/createAbsencePeriod";
import { createMockManagedRequirement } from "lib/mock-helpers/createMockManagedRequirement";
import { faker } from "@faker-js/faker";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

const absencePeriodTypes: Array<AbsencePeriod["period_type"]> = [
  "Continuous",
  "Reduced Schedule",
  "Intermittent",
];

export default {
  title: "Pages/Employers/Applications/Review",
  component: Review,
  argTypes: {
    "Absence period reasons": {
      control: {
        type: "check",
        options: Object.values(LeaveReason),
      },
    },
    "Absence period types": {
      control: {
        type: "check",
        options: absencePeriodTypes,
      },
    },
    "Includes documentation": {
      control: {
        type: "boolean",
        options: ["Yes", "No"],
      },
    },
    "Number of absence periods for each leave reason": {
      control: {
        type: "number",
      },
    },
    // Todo(EMPLOYER-1453): remove V1 eform functionality
    "Claimant EForm Version": {
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
    "Reviewed Previously": {
      control: {
        type: "radio",
        options: ["No", "Yes, via Portal", "Yes, via contact center"],
      },
    },
  },
  args: {
    "Absence period reasons": [LeaveReason.medical],
    "Absence period types": [absencePeriodTypes[0]],
    "Claimant EForm Version": "Version 2 (after 2021-07-14)",
    "Includes documentation": true,
    "Number of absence periods for each leave reason": 1,
    "Reviewed Previously": "No",
  },
};

export const Default = (
  args: Props<typeof Review> & {
    "Absence period reasons": LeaveReasonType[];
    "Absence period types": Array<AbsencePeriod["period_type"]>;
    "Claimant EForm Version": string;
    "Includes documentation": boolean;
    "Number of absence periods for each leave reason": number;
    "Reviewed Previously": string;
    errorTypes: string[];
  }
) => {
  // Add fallbacks in case the user unchecked all the checkboxes, which would
  // cause a JS exception if left empty:
  const selectedLeaveReasons: LeaveReasonType[] = args["Absence period reasons"]
    .length
    ? args["Absence period reasons"]
    : [LeaveReason.medical];

  const managedRequirements: ManagedRequirement[] = [
    createMockManagedRequirement({
      follow_up_date: "2021-12-10",
      status: "Open",
    }),
    createMockManagedRequirement({
      follow_up_date: "2021-08-30",
      responded_at:
        args["Reviewed Previously"] === "Yes, via Portal" ? "2021-10-01" : "",
      status: args["Reviewed Previously"] !== "No" ? "Complete" : "Suppressed",
    }),
  ];

  const selectedLeaveTypes: Array<AbsencePeriod["period_type"]> = args[
    "Absence period types"
  ].length
    ? args["Absence period types"]
    : ["Continuous"];

  const claim = createEmployerClaimFromArgs({
    ...args,
    "Absence period reasons": selectedLeaveReasons,
    "Absence period types": selectedLeaveTypes,
    "Managed Requirements": managedRequirements,
  });

  const errorTypes = args.errorTypes || [];
  const documents = args["Includes documentation"]
    ? args["Absence period reasons"]
        .map((reason) => createCertificationDocumentForReason(reason))
        .filter((d) => d !== null)
    : [];

  const appLogic = useMockableAppLogic({
    errors: [new ValidationError(getErrorInfoCollection(errorTypes))],
    employers: {
      claimDocumentsMap: new Map([
        [
          claim.fineos_absence_id,
          new ApiResourceCollection<ClaimDocument>(
            "fineos_document_id",
            documents as ClaimDocument[]
          ),
        ],
      ]),
    },
  });

  return <Review appLogic={appLogic} claim={claim} user={new User({})} />;
};

function createEmployerClaimFromArgs(args: {
  "Absence period reasons": LeaveReasonType[];
  "Absence period types": Array<AbsencePeriod["period_type"]>;
  "Claimant EForm Version": string;
  "Number of absence periods for each leave reason": number;
  "Managed Requirements": ManagedRequirement[];
}): EmployerClaim {
  // Generate one absence period for each selected leave reason
  const absence_periods: AbsencePeriod[] = [];
  args["Absence period reasons"].forEach((reason: LeaveReasonType) => {
    Array.from(
      Array(args["Number of absence periods for each leave reason"])
    ).forEach(() => {
      absence_periods.push(
        createAbsencePeriod({
          reason,
          period_type: faker.random.arrayElement(args["Absence period types"]),
        })
      );
    });
  });

  let claimBuilder = new MockEmployerClaimBuilder()
    .completed()
    .previousLeaves();

  if (args["Claimant EForm Version"] === "Version 1 (before 2021-07-14)") {
    claimBuilder = claimBuilder.eformsV1();
  } else {
    claimBuilder = claimBuilder.eformsV2().concurrentLeave();
  }

  const claim = claimBuilder.create();
  claim.absence_periods = absence_periods;

  // TODO (PORTAL-1117): leave_details will be removed in the future
  claim.leave_details = {
    ...claim.leave_details,
    reason: absence_periods[0].reason,
    continuous_leave_periods: absence_periods
      .filter((period) => period.period_type === "Continuous")
      .map((period) => ({
        start_date: period.absence_period_start_date,
        end_date: period.absence_period_end_date,
      })),
    reduced_schedule_leave_periods: absence_periods
      .filter((period) => period.period_type === "Reduced Schedule")
      .map((period) => ({
        start_date: period.absence_period_start_date,
        end_date: period.absence_period_end_date,
      })),
    intermittent_leave_periods: absence_periods
      .filter((period) => period.period_type === "Intermittent")
      .map((period) => ({
        leave_period_id: period.fineos_leave_request_id,
        start_date: period.absence_period_start_date,
        end_date: period.absence_period_end_date,
        duration: 1,
        duration_basis: "Days",
        frequency: 1,
        frequency_interval: null,
        frequency_interval_basis: "Weeks",
      })),
  };

  claim.managed_requirements = args["Managed Requirements"];
  return claim;
}

function createCertificationDocumentForReason(
  leaveReason: LeaveReasonType
): ClaimDocument | null {
  if (!(leaveReason in DocumentType.certification)) {
    return null;
  }

  const document: ClaimDocument = {
    content_type: "application/pdf",
    created_at: "2020-01-02",
    description: "Mock document description",
    document_type:
      DocumentType.certification[
        leaveReason as keyof typeof DocumentType.certification
      ],
    fineos_document_id: faker.datatype.uuid(),
    name: `${leaveReason} document`,
  };

  return document;
}

function getErrorInfoCollection(errorTypes: string[] = []) {
  const errors = [];

  if (errorTypes.includes("Hours worked per week - minimum")) {
    errors.push({
      type: "minimum",
      field: "hours_worked_per_week",
      namespace: "employers",
    });
  }

  if (errorTypes.includes("Hours worked per week - maximum")) {
    errors.push({
      type: "maximum",
      field: "hours_worked_per_week",
      namespace: "employers",
    });
  }

  if (errorTypes.includes("Employer benefit - benefit end date")) {
    errors.push({
      type: "minimum",
      field: "employer_benefits[0].benefit_end_date",
      namespace: "employers",
    });
  }

  if (errorTypes.includes("Previous leave - leave start date")) {
    errors.push({
      type: "invalid_previous_leave_start_date",
      field: "previous_leaves[0].leave_start_date",
      namespace: "employers",
    });
  }

  if (errorTypes.includes("Previous leave - leave end date")) {
    errors.push({
      type: "minimum",
      field: "previous_leaves[0].leave_end_date",
      namespace: "employers",
    });
  }

  return errors;
}
