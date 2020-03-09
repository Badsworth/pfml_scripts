import AuthNav from "./AuthNav";
import React from "react";

export default {
  title: "AuthNav",
  component: AuthNav,
};

export const WithUser = () => <AuthNav user={{ username: "Bud Baxter" }} />;
