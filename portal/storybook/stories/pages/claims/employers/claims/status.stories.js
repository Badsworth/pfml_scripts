import React from "react";
import { Status } from "src/pages/employers/claims/status";
import User from "src/models/User";

export default {
  title: "Pages/Employers/Claims/Status",
  component: Status,
};

export const Default = () => {
  const user = new User();
  const appLogic = {
    setAppErrors: () => {},
  };
  return <Status appLogic={appLogic} user={user} />;
};
