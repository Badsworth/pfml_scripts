import ClaimDetail, { AbsencePeriod } from "src/models/ClaimDetail";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import DocumentCollection from "src/models/DocumentCollection";
import DocumentUploadIndex from "src/pages/applications/upload/index";
import LeaveReason from "src/models/LeaveReason";
import React from "react";
import { pick } from "lodash";

const absencePeriodScenarios = {
  bondingWithNewBorn: new AbsencePeriod({
    reason: LeaveReason.bonding,
    reason_qualifier_one: "Newborn",
  }),
  bondingWithFoster: new AbsencePeriod({
    reason: LeaveReason.bonding,
    reason_qualifier_one: "Foster Care",
  }),
  bondingWithAdoption: new AbsencePeriod({
    reason: LeaveReason.bonding,
    reason_qualifier_one: "Adoption",
  }),
  medical: new AbsencePeriod({ reason: LeaveReason.medical }),
  pregnancy: new AbsencePeriod({ reason: LeaveReason.pregnancy }),
  caring: new AbsencePeriod({ reason: LeaveReason.care }),
};

export default {
  title: "Pages/Applications/Upload/Index",
  component: DocumentUploadIndex,
  argTypes: {
    absencePeriod: {
      options: Object.keys(absencePeriodScenarios),
      control: {
        type: "check",
        labels: {
          bondingWithNewBorn: "Bonding with new born",
          bondingWithFoster: "Bonding with foster",
          bondingWithAdoption: "Bonding with adoption",
          medical: "Medical",
          pregnancy: "Pregnancy",
          caring: "Caring",
        },
      },
    },
  },
};

const appLogic = {
  benefitsApplications: {
    update: () => {},
  },
  documents: {
    attachDocument: () => {},
    documents: new DocumentCollection([]),
  },
  appErrors: new AppErrorInfoCollection(),
  setAppErrors: () => {},
  catchError: () => {},
  claims: {
    claimDetail: new ClaimDetail(),
    loadClaimDetail: () => {},
  },
  clearErrors: () => {},
  portalFlow: {
    goToNextPage: () => "/storybook-mock",
  },
};

export const Default = ({ absencePeriod, ...args }) => {
  appLogic.claims.claimDetail = new ClaimDetail({
    application_id: "application-id",
    fineos_absence_id: "fineos-absence-id",
    absence_periods: Object.values(pick(absencePeriodScenarios, absencePeriod)),
  });

  return (
    <DocumentUploadIndex
      {...args}
      appLogic={appLogic}
      documents={[]}
      query={{ absence_case_id: "mock-absence-id" }}
    />
  );
};
