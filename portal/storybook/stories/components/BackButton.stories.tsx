import BackButton from "src/components/BackButton";
import { Props } from "types/common";
import React from "react";
import Title from "src/components/core/Title";

class MockHistory {
  back() {}

  get length() {
    return 2;
  }
}

export default {
  title: "Components/BackButton",
  component: BackButton,
  // Simulate browser history so the back button renders!
  args: {
    history: new MockHistory(),
  },
};

export const Example = (args: Props<typeof BackButton>) => (
  <BackButton {...args} />
);

export const SpacingBetweenLargeTitle = (args: Props<typeof BackButton>) => (
  <React.Fragment>
    <BackButton {...args} />
    <Title>Page title</Title>
  </React.Fragment>
);

export const SpacingBetweenSmallTitle = (args: Props<typeof BackButton>) => (
  <React.Fragment>
    <BackButton {...args} />
    <Title small>Page title</Title>
  </React.Fragment>
);

export const CustomLabelAndLink = (args: Props<typeof BackButton>) => (
  <React.Fragment>
    <BackButton label="Custom Label" href="#" {...args} />
    <Title small>Page title</Title>
  </React.Fragment>
);
