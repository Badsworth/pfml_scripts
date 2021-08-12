import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { ApplicationCardV2 } from "src/components/ApplicationCardV2";
import BenefitsApplication from "src/models/BenefitsApplication";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import React from "react";

export default {
  title: "Components/ApplicationCardV2",
  component: ApplicationCardV2,
  argTypes: {
    claim: {
      defaultValue: "Completed",
      control: {
        type: "radio",
        options: ["Completed"],
      },
    },
  },
};

export const Story = ({ claim, _documents, ...args }) => {
  const attachedDocuments = [],
    errors = [];
  const claimAttrs = {
    Completed: new MockBenefitsApplicationBuilder().completed().create(),
  }[claim];

  const appLogic = {
    appErrors: new AppErrorInfoCollection(errors),
    documents: {
      download: () => {},
    },
  };

  return (
    <ApplicationCardV2
      appLogic={appLogic}
      claim={new BenefitsApplication(claimAttrs)}
      {...args}
      documents={attachedDocuments}
    />
  );
};
