import ApiResourceCollection from "src/models/ApiResourceCollection";
import BenefitsApplication from "src/models/BenefitsApplication";
import { GetReady } from "src/pages/applications/get-ready";
import PaginationMeta from "src/models/PaginationMeta";
import React from "react";
import User from "src/models/User";
import routes from "src/routes";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: `Pages/Applications/Get Ready`,
  component: GetReady,
  argTypes: {
    smsMfaConfirmed: {
      control: {
        type: "boolean",
      },
    },
  },
  args: {
    smsMfaConfirmed: false,
  },
};

export const Page = (args: { smsMfaConfirmed: boolean }) => {
  const appLogic = useMockableAppLogic({
    portalFlow: {
      pathname: routes.applications.getReady,
    },
  });

  const paginationMeta: PaginationMeta = {
    page_offset: 1,
    total_pages: 1,
    order_by: "",
    order_direction: "ascending",
    page_size: 25,
    total_records: 20,
  };

  const query = args.smsMfaConfirmed ? { smsMfaConfirmed: "true" } : {};

  return (
    <GetReady
      claims={new ApiResourceCollection<BenefitsApplication>("application_id")}
      appLogic={appLogic}
      user={new User({})}
      paginationMeta={paginationMeta}
      query={query}
    />
  );
};
