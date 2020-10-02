import React from "react";
import { Success } from "src/pages/employers/claims/success";

export default {
  title: `Pages/Employers/Claims/Success`,
  component: Success,
};

export const Default = () => {
  const query = {
    absence_id: "NTN-111-ABS-01",
  };
  return <Success query={query} />;
};
