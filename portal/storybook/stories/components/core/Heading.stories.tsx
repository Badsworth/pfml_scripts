import Heading from "src/components/core/Heading";
import HeadingPrefix from "src/components/core/HeadingPrefix";
import React from "react";
import Title from "src/components/core/Title";

export default {
  title: "Core Components/Heading",
  component: Heading,
};

export const Default = () => (
  <React.Fragment>
    <Title>Page headings</Title>
    <Heading level="2">Level 2 (h2): Your account has been created</Heading>
    <Heading level="3">Level 3 (h3): Your account has been created</Heading>
    <Heading level="4">Level 4 (h4): Your account has been created</Heading>
    <Heading level="5">Level 5 (h5): Your account has been created</Heading>
    <Heading level="6">Level 6 (h6): Your account has been created</Heading>
  </React.Fragment>
);

export const WithPrefix = () => (
  <Heading level="2" size="1">
    <HeadingPrefix>Part 1</HeadingPrefix>
    Tell us about yourself and your leave
  </Heading>
);

export const CustomSizes = () => (
  <React.Fragment>
    <Heading level="2" size="3">
      Level 2 as Size 3: Your account has been created
    </Heading>
    <Heading level="3" size="2">
      Level 3 as Size 2: Your account has been created
    </Heading>
    <Heading level="4" size="3">
      Level 4 as Size 3: Your account has been created
    </Heading>
    <Heading level="5" size="4">
      Level 5 as Size 4: Your account has been created
    </Heading>
    <Heading level="6" size="5">
      Level 6 as Size 5: Your account has been created
    </Heading>
  </React.Fragment>
);
