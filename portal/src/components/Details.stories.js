import Details from "./Details";
import React from "react";

export default {
  title: "Components/Details",
  component: Details,
};

export const Default = () => (
  <Details label="Label">
    <h1>Some content</h1>
  </Details>
);
