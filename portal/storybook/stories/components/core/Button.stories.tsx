/* eslint-disable no-alert */
import Button from "src/components/core/Button";
import { Props } from "types/common";
import React from "react";

export default {
  title: "Core Components/Button",
  component: Button,
  args: {
    children: "Submit",
  },
};

export const Default = ({ children, ...args }: Props<typeof Button>) => {
  const handleClick = () => alert("Clicked!");

  return (
    <Button {...args} onClick={handleClick}>
      {children}
    </Button>
  );
};

export const Disabled = () => {
  const handleClick = () => alert("Clicked!");

  return (
    <Button onClick={handleClick} disabled>
      Submit
    </Button>
  );
};

export const Loading = () => {
  const handleClick = () => alert("Clicked!");

  return (
    <Button onClick={handleClick} loading>
      Loading
    </Button>
  );
};

export const LoadingMessage = () => {
  const handleClick = () => alert("Clicked!");

  return (
    <Button onClick={handleClick} loading loadingMessage="Saving. Please wait.">
      Loading
    </Button>
  );
};

export const Variations = () => {
  const handleClick = () => alert("Clicked!");

  return (
    <React.Fragment>
      <Button onClick={handleClick}>default</Button>
      <Button onClick={handleClick} variation="accent-cool">
        accent-cool
      </Button>
      <Button onClick={handleClick} variation="outline">
        outline
      </Button>
      <Button onClick={handleClick} variation="secondary">
        secondary
      </Button>
      <Button onClick={handleClick} variation="unstyled">
        unstyled
      </Button>
      <div className="bg-ink padding-2 margin-top-2">
        <Button onClick={handleClick} inversed variation="outline">
          Inversed outline
        </Button>
        <Button onClick={handleClick} inversed variation="unstyled">
          Inversed unstyled
        </Button>
      </div>
    </React.Fragment>
  );
};
