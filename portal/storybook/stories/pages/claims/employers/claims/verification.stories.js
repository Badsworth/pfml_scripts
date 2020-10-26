import React from "react";
import User from "src/models/User";
import { Verification } from "src/pages/employers/claims/verification";

export default {
  title: "Pages/Employers/Claims/Verification",
  component: Verification,
};

export const Default = () => {
  const user = new User();
  const appLogic = {
    setAppErrors: () => {},
  };
  const query = {
    absence_id: "mock-absence-id",
  };
  return <Verification appLogic={appLogic} query={query} user={user} />;
};
