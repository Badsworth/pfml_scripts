import React from "react";
import { Review } from "src/pages/employers/claims/review";
import User from "src/models/User";

export default {
  title: `Pages/Employers/Claims/Review`,
  component: Review,
};

export const Default = () => {
  const user = new User();
  const appLogic = {
    setAppErrors: () => {},
  };
  return <Review appLogic={appLogic} user={user} />;
};
