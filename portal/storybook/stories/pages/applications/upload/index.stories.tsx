import { AbsencePeriod } from "src/models/AbsencePeriod";
import ClaimDetail from "src/models/ClaimDetail";
import DocumentUploadIndex from "src/pages/applications/upload/index";
import LeaveReason from "src/models/LeaveReason";
import React from "react";
import { faker } from "@faker-js/faker";
import { pick } from "lodash";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

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

export const Default = ({ absencePeriod }: { absencePeriod: string }) => {
  const claimDetail = new ClaimDetail({
    application_id: "application-id",
    fineos_absence_id: "fineos-absence-id",
    absence_periods: Object.values(
      pick(absencePeriodScenarios, absencePeriod ?? "medical")
    ),
    employee: null,
    employer: null,
    fineos_notification_id: faker.datatype.uuid(),
    managed_requirements: [],
    outstanding_evidence: null,
  });

  const appLogic = useMockableAppLogic({
    claims: {
      claimDetail,
    },
  });

  return (
    <DocumentUploadIndex
      appLogic={appLogic}
      query={{ absence_id: claimDetail.fineos_absence_id }}
    />
  );
};
