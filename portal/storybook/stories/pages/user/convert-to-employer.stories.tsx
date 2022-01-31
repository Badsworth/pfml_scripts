import ApiResourceCollection from "src/models/ApiResourceCollection";
import BenefitsApplication from "src/models/BenefitsApplication";
import { ConvertToEmployer } from "src/pages/user/convert-to-employer";
import PaginationMeta from "src/models/PaginationMeta";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/User/Convert to Employer",
  component: ConvertToEmployer,
};

const paginationMeta: PaginationMeta = {
  page_offset: 1,
  total_pages: 1,
  order_by: "",
  order_direction: "ascending",
  page_size: 25,
  total_records: 20,
};

export const Page = () => {
  const user = new User({});
  const claims = new ApiResourceCollection<BenefitsApplication>(
    "application_id"
  );
  const appLogic = useMockableAppLogic();

  return (
    <ConvertToEmployer
      appLogic={appLogic}
      user={user}
      claims={claims}
      paginationMeta={paginationMeta}
    />
  );
};
