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

export const Default = ({ type }) => (
  <DocumentRequirements type={type} role="complementary" />
);
