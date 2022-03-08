import ApiResourceCollection from "src/models/ApiResourceCollection";
import BenefitsApplication from "src/models/BenefitsApplication";
import { Index } from "src/pages/applications/index";
import React from "react";
import User from "src/models/User";
import { createMockBenefitsApplication } from "lib/mock-helpers/createMockBenefitsApplication";
import { faker } from "@faker-js/faker";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

const queries = {
  Default: {},
  ApplicationAssociated: { applicationAssociated: "NTN-111-ABS-0" },
  SmsMfaConfirmed: { smsMfaConfirmed: "true" },
  UploadedAbsenceId: { uploadedAbsenceId: "NTN-111-ABS-0" },
};

export default {
  title: "Pages/Applications/Index",
  component: Index,
  argTypes: {
    query: {
      control: {
        type: "radio",
        options: Object.keys(queries),
      },
    },
  },
  args: {
    total_pages: 2,
    query: "Default",
  },
};

export const Default = (args: {
  total_pages: number;
  query: keyof typeof queries;
}) => {
  const claims = [];
  for (let i = 0; i < 10; i++) {
    const claim = createMockBenefitsApplication(
      faker.random.arrayElement(["submitted", "completed"]),
      faker.random.arrayElement(["medicalLeaveReason", "bondingLeaveReason"])
    );
    claim.application_id = `${i}`;
    claim.fineos_absence_id = `NTN-111-ABS-${i}`;
    claims.push(claim);
  }

  const user = new User({});

  const appLogic = useMockableAppLogic({
    documents: {
      isLoadingClaimDocuments: () => false,
    },
    benefitsApplications: {
      benefitsApplications: new ApiResourceCollection<BenefitsApplication>(
        "application_id",
        claims
      ),
      isLoadingClaims: false,
      paginationMeta: {
        page_offset: 1,
        page_size: 25,
        total_pages: args.total_pages ? args.total_pages : 1,
        total_records: claims.length,
        order_by: "created_at",
        order_direction: "ascending",
      },
    },
  });

  const query = queries[args.query];

  return <Index appLogic={appLogic} user={user} query={query} />;
};

// This update is currently behind the splitClaimsAcrossBY
// which will need to be enabled to see the new content
export const WithBenefitYearNotice = (args: {
  total_pages: number;
  query: keyof typeof queries;
}) => {
  const claims = [];
  for (let i = 0; i < 10; i++) {
    const claim = createMockBenefitsApplication(
      faker.random.arrayElement(["submitted", "completed"]),
      faker.random.arrayElement(["medicalLeaveReason", "bondingLeaveReason"])
    );
    claim.application_id = `${i}`;
    claim.fineos_absence_id = `NTN-111-ABS-${i}`;
    claims.push(claim);
  }

  const user = new User({});

  const appLogic = useMockableAppLogic({
    documents: {
      isLoadingClaimDocuments: () => false,
    },
    benefitYears: {
      getCurrentBenefitYear: () => ({
        benefit_year_end_date: new Date().toISOString(),
        benefit_year_start_date: new Date().toISOString(),
        employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
        current_benefit_year: true,
      }),
    },
    benefitsApplications: {
      benefitsApplications: new ApiResourceCollection<BenefitsApplication>(
        "application_id",
        claims
      ),
      isLoadingClaims: false,
      paginationMeta: {
        page_offset: 1,
        page_size: 25,
        total_pages: args.total_pages ? args.total_pages : 1,
        total_records: claims.length,
        order_by: "created_at",
        order_direction: "ascending",
      },
    },
  });

  const query = queries[args.query];

  return <Index appLogic={appLogic} user={user} query={query} />;
};
