/* eslint-disable no-alert */
import Button from "./Button";
import React from "react";

export default {
  title: "Components/Buttons/Button",
  component: Button,
};

export const Default = () => {
  const handleClick = () => alert("Clicked!");

  return <Button onClick={handleClick}>Submit</Button>;
};

export const Disabled = () => {
  const handleClick = () => alert("Clicked!");

  return (
    <Button onClick={handleClick} disabled>
      Submit
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
      </div>
    </React.Fragment>
  );
};
