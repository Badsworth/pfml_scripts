import Heading from "src/components/Heading";
import HeadingPrefix from "src/components/HeadingPrefix";
import React from "react";

export default {
  title: "Components/HeadingPrefix",
  component: HeadingPrefix,
};

export const Default = () => <HeadingPrefix>Part 1</HeadingPrefix>;

export const Nested = () => (
  <Heading level="2" size="1">
    <HeadingPrefix>Part 1</HeadingPrefix>
    Tell us about yourself and your leave
  </Heading>
);
