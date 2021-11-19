import { BenefitsApplicationDocument, DocumentType } from "src/models/Document";
import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import DocumentCollection from "src/models/DocumentCollection";
import EmployerClaim from "src/models/EmployerClaim";
import { Props } from "storybook/types";
import React from "react";
import { Review } from "src/pages/employers/applications/review";
import User from "src/models/User";
import { createMockEmployerClaim } from "tests/test-utils/createMockEmployerClaim";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Employers/Applications/Review",
  component: Review,
  argTypes: {
    claimOption: {
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
      control: {
        type: "radio",
        options: ["Bonding", "Medical", "Care", "Pregnancy"],
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
  },
  args: {
    claimOption: "Continuous or reduced - documentation",
    "Leave reason": "Medical",
    "Claimant EForm Version": "Version 2 (after 2021-07-14)",
  },
};

type DocumentationOption = "documentation" | "without documentation";

export const Default = (
  args: Props<typeof Review> & {
    claimOption: `${string} - ${DocumentationOption}`;
    "Claimant EForm Version": string;
    errorTypes: string[];
    "Leave reason": string;
  }
) => {
  const { claimOption } = args;
  const errorTypes = args.errorTypes || [];
  const documentationOption = claimOption.split("-")[1] as DocumentationOption;

  const leaveReason = {
    Bonding: "bondingLeaveReason",
    Medical: "medicalLeaveReason",
    Care: "caringLeaveReason",
    Pregnancy: "pregnancyLeaveReason",
  }[args["Leave reason"]];

  const formVersion: string[] | undefined =
    {
      "Version 1 (before 2021-07-14)": ["eformsV1"],
      "Version 2 (after 2021-07-14)": ["eformsV2", "concurrentLeave"],
    }[args["Claimant EForm Version"]] || [];

  const optionText = claimOption.toLowerCase();
  const leaveTypes = [
    optionText.includes("continuous") && "continuous",
    optionText.includes("intermittent") && "intermittent",
    optionText.includes("reduced") && "reducedSchedule",
  ].filter((text) => text); // removes falsy values

  const claim = createMockEmployerClaim(
    "completed",
    "previousLeaves",
    "reviewable",
    leaveReason,
    ...formVersion,
    ...leaveTypes
  ) as EmployerClaim;

  const appLogic = useMockableAppLogic({
    appErrors: getAppErrorInfoCollection(errorTypes),
    employers: {
      claimDocumentsMap: getDocumentsMap(
        documentationOption,
        claim.leave_details.reason,
        claim.fineos_absence_id
      ),
    },
  });

  return <Review appLogic={appLogic} claim={claim} user={new User({})} />;
};

function getDocumentsMap(
  documentation: DocumentationOption,
  leaveReason: string | null,
  absenceId: string
) {
  const isWithoutDocumentation = documentation.includes(
    "without documentation"
  );

  if (
    isWithoutDocumentation ||
    !leaveReason ||
    !(leaveReason in DocumentType.certification)
  ) {
    return new Map([[absenceId, new DocumentCollection()]]);
  }

  const documentData: BenefitsApplicationDocument = {
    application_id: "mock-application-id",
    content_type: "application/pdf",
    created_at: "2020-01-02",
    description: "",
    document_type:
      DocumentType.certification[
        leaveReason as keyof typeof DocumentType.certification
      ],
    fineos_document_id: "202020",
    name: `${leaveReason} document`,
    user_id: "",
  };

  return new Map([[absenceId, new DocumentCollection([documentData])]]);
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
