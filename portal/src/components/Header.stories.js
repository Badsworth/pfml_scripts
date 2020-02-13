import Header from "./Header";
import React from "react";

export default {
  title: "Header",
  component: Header
};

export const WithUser = () => <Header user={{ username: "Bud Baxter" }} />;
