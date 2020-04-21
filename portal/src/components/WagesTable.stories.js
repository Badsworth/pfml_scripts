import React from "react";
import WagesTable from "./WagesTable";

export default {
  title: "Screens/Eligibility Result/WagesTable",
  component: WagesTable,
};

export const Eligible = () => (
  <WagesTable employeeId="1234-55-66-7777" eligibility="eligible" />
);

export const Ineligible = () => (
  <WagesTable employeeId="1234-55-66-7777" eligibility="ineligible" />
);
