import ButtonLink from "./ButtonLink";
import React from "react";

const href = "http://www.example.com";

export default {
  title: "Components/Buttons/ButtonLink",
  component: ButtonLink,
};

export const Default = () => {
  return <ButtonLink href={href}>Click here</ButtonLink>;
};

export const Outline = () => {
  return (
    <ButtonLink href={href} variation="outline">
      Click here
    </ButtonLink>
  );
};

export const Secondary = () => {
  return (
    <ButtonLink href={href} variation="secondary">
      Click here
    </ButtonLink>
  );
};

export const AccentCool = () => {
  return (
    <ButtonLink href={href} variation="accent-cool">
      Click here
    </ButtonLink>
  );
};

export const Disabled = () => {
  return (
    <ButtonLink href={href} disabled>
      Click here
    </ButtonLink>
  );
};
