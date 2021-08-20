import Document, { DocumentType } from "src/models/Document";

import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { ApplicationCardV2 } from "src/components/ApplicationCardV2";
import BenefitsApplication from "src/models/BenefitsApplication";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import React from "react";
import { uniqueId } from "lodash";

export default {
  title: "Components/ApplicationCardV2",
  component: ApplicationCardV2,
  args: {
    number: 1,
  },
  argTypes: {
    claim: {
      defaultValue: "In Progress + Notices",
      control: {
        type: "radio",
        options: ["Completed", "In Progress", "In Progress + Notices"],
      },
    },
  },
};

export const Story = ({ claim, ...args }) => {
  // Generates claim of type (e.g., completed)
  const generateClaim = (type) => {
    return new BenefitsApplication(
      new MockBenefitsApplicationBuilder()[type]().create()
    );
  };

  // Generates notice of type (e.g., denialNotice)
  const generateNotice = (type) => {
    // Creates random number up to limit {number} value
    const createRandomInteger = (limit) => {
      const randomNumber = Math.floor(Math.random() * limit) + 1;
      return `0${randomNumber}`.slice(-2);
    };

    // Four-digit prior year (e.g., 2020)
    const lastYear = new Date().getFullYear() - 1;

    // Random month/day for notice date
    const randomMonth = createRandomInteger(12);
    const randomDay = createRandomInteger(28);

    return new Document({
      created_at: `${lastYear}-${randomMonth}-${randomDay}`,
      document_type: DocumentType[type],
      fineos_document_id: uniqueId("notice"),
    });
  };

  // Fake appLogic for stories
  const appLogic = {
    appErrors: new AppErrorInfoCollection([]),
    documents: {
      download: () => {},
    },
  };

  // Configuration for ApplicationCard props
  const cardProps = Object.assign(
    {
      Completed: {
        claim: generateClaim("completed"),
      },

      "In Progress + Notices": {
        claim: generateClaim("submitted"),
        documents: [
          generateNotice("requestForInfoNotice"),
          generateNotice("denialNotice"),
        ],
      },

      "In Progress": {
        claim: generateClaim("employed"),
      },
    }[claim],
    { appLogic, ...args }
  );

  return <ApplicationCardV2 {...cardProps} />;
};
