import BackButton from "src/components/BackButton";
import React from "react";
import Title from "src/components/core/Title";

export default {
  title: "Components/BackButton",
  component: BackButton,
};

export const Example = () => <BackButton />;

export const SpacingBetweenLargeTitle = () => (
  <React.Fragment>
    <BackButton />
    <Title>Page title</Title>
  </React.Fragment>
);

export const SpacingBetweenSmallTitle = () => (
  <React.Fragment>
    <BackButton />
    <Title small>Page title</Title>
  </React.Fragment>
);

export const CustomLabelAndLink = () => (
  <React.Fragment>
    <BackButton label="Custom Label" href="#" />
    <Title small>Page title</Title>
  </React.Fragment>
);
