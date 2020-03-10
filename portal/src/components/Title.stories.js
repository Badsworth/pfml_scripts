import React from "react";
import Title from "./Title";

export default {
  title: "Pages|Title",
  component: Title,
};

export const Default = () => <Title>Verify your employment history</Title>;

export const Legend = () => (
  <Title component="legend">Where do you receive mail?</Title>
);
