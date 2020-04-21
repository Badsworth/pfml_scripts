import BackButton from "./BackButton";
import React from "react";
import Title from "./Title";

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
