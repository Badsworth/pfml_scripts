import React from "react";
import { Success } from "src/pages/employers/applications/success";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: `Pages/Employers/Applications/Success`,
  component: Success,
};

export const Default = () => {
  const query = {
    absence_id: "NTN-111-ABS-01",
  };
  const appLogic = useMockableAppLogic();

  return <Success query={query} appLogic={appLogic} user={new User({})} />;
};
