import { Confirmation } from "src/pages/employers/claims/confirmation";
import React from "react";

export default {
  title: "Pages/Employers/Claims/Confirmation",
  component: Confirmation,
};

export const Default = () => {
  const query = {
    absence_id: "NTN-1315-ABS-01",
    due_date: "2022-01-01",
  };
  return <Confirmation query={query} />;
};
