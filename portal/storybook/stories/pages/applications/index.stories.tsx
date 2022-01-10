import BenefitsApplicationCollection from "src/models/BenefitsApplicationCollection";
import { Index } from "src/pages/applications/index";
import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

const queries = {
  Default: {},
  SmsMfaConfirmed: { smsMfaConfirmed: "true" },
  UploadedAbsenceId: { uploadedAbsenceId: "NTN-111-ABS-01" },
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
  const claims = () => {
    const inProgressClaims = [];
    const completedClaims = [];
    for (let i = 0; i < 10; i++) {
      inProgressClaims.push(
        new MockBenefitsApplicationBuilder().id(i).create()
      );
      completedClaims.push(
        new MockBenefitsApplicationBuilder()
          .completed()
          .id(i * 10)
          .create()
      );
    }

    return [...inProgressClaims, ...completedClaims];
  };

  const user = new User({});

  const appLogic = useMockableAppLogic({
    benefitsApplications: {
      benefitsApplications: new BenefitsApplicationCollection(claims()),
      isLoadingClaims: false,
      paginationMeta: {
        page_offset: 1,
        page_size: 25,
        total_pages: args.total_pages ? args.total_pages : 1,
        total_records: claims().length,
        order_by: "created_at",
        order_direction: "ascending",
      },
    },
  });

  const query = queries[args.query];

  return <Index appLogic={appLogic} user={user} query={query} />;
};
