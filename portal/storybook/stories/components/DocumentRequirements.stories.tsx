import DocumentRequirements from "src/components/DocumentRequirements";
import React from "react";

export default {
  title: "Components/DocumentRequirements",
  component: DocumentRequirements,
  argTypes: {
    type: {
      defaultValue: "id",
      control: {
        type: "radio",
        options: ["id", "certification"],
      },
    },
  },
};

// @ts-expect-error ts-migrate(7031) FIXME: Binding element 'type' implicitly has an 'any' typ... Remove this comment to see the full error message
export const Default = ({ type }) => (
  // @ts-expect-error ts-migrate(2322) FIXME: Type '{ type: any; role: string; }' is not assigna... Remove this comment to see the full error message
  <DocumentRequirements type={type} role="complementary" />
);
