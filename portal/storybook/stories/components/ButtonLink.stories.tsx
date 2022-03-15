import ButtonLink from "src/components/ButtonLink";
import React from "react";

const href = "http://www.example.com";

export default {
  title: "Components/ButtonLink",
  component: ButtonLink,
};

export const Default = () => {
  return <ButtonLink href={href}>Click here</ButtonLink>;
};

export const Disabled = () => {
  return (
    <ButtonLink href={href} disabled>
      Click here
    </ButtonLink>
  );
};

export const Variations = () => {
  return (
    <React.Fragment>
      <ButtonLink href={href}>default</ButtonLink>
      <ButtonLink href={href} variation="accent-cool">
        accent-cool
      </ButtonLink>
      <ButtonLink href={href} variation="outline">
        outline
      </ButtonLink>
      <ButtonLink href={href} variation="secondary">
        secondary
      </ButtonLink>
      <ButtonLink href={href} variation="unstyled">
        unstyled
      </ButtonLink>
      <div className="bg-ink padding-2 margin-top-2">
        <ButtonLink href={href} inversed variation="outline">
          Inversed outline
        </ButtonLink>
        <ButtonLink href={href} inversed variation="unstyled">
          Inversed unstyled
        </ButtonLink>
      </div>
    </React.Fragment>
  );
};
