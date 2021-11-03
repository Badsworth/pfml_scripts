import { rest, setupWorker } from "msw";
import { Address } from "src/pages/applications/address";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import React from "react";

export default {
  title: `Pages/Applications/Address`,
  component: Address,
  argTypes: {
    validationResult: {
      options: ["None", "Multiple matches", "No matches"],
      control: { type: "radio" },
      defaultValue: "None",
    },
  },
};

export const Default = ({ validationResult, ...args }) => {
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    catchError: () => {},
    benefitsApplications: {
      update: () => {},
    },
  };

  const claimBuilder = new MockBenefitsApplicationBuilder();

  if (validationResult === "No matches") {
    claimBuilder.address({ line_2: "No matches" });
  } else if (validationResult === "Multiple matches") {
    claimBuilder.address({ line_2: "Multiple matches" });
  } else {
    claimBuilder.address({});
  }

  return (
    <Address {...args} appLogic={appLogic} claim={claimBuilder.create()} />
  );
};

const mockSearchMultipleMatches = (req, res, ctx) => {
  return res(
    ctx.json({
      result: {
        more_results_available: false,
        confidence: "Multiple matches",
        suggestions: [
          {
            global_address_key: "mockaddresskeyapt1",
            matched: [],
            text: "54321 Mock Address Apt 1 Washington, DC 20005",
            format:
              "https://api.experianaperture.io/address/format/v1/mockaddresskeyapt1",
          },
          {
            global_address_key: "mockaddresskeyapt2",
            matched: [],
            text: "54321 Mock Address Apt 2 Washington, DC 20005",
            format:
              "https://api.experianaperture.io/address/format/v1/mockaddresskeyapt2",
          },
        ],
      },
    })
  );
};

const mockSearchNoMatches = (req, res, ctx) => {
  return res(
    ctx.json({
      result: {
        more_results_available: false,
        confidence: "No matches",
        suggestions: [],
      },
    })
  );
};

const mockSearchRequest = (req, res, ctx) => {
  const address = req.body.components.unspecified[0];

  if (address.includes("Multiple matches")) {
    return mockSearchMultipleMatches(req, res, ctx);
  }

  if (address.includes("No matches")) {
    return mockSearchNoMatches(req, res, ctx);
  }

  return res(
    ctx.json({
      result: {
        more_results_available: false,
        confidence: "Verified match",
        suggestions: [
          {
            global_address_key: "mockaddresskeyapt1",
            matched: [],
            text: "54321 Mock Address Apt 1 Washington, DC 20005",
            format:
              "https://api.experianaperture.io/address/format/v1/mockaddresskeyapt1",
          },
        ],
      },
    })
  );
};

const mockFormatRequest = (req, res, ctx) => {
  return res(
    ctx.json({
      result: {
        global_address_key: req.params.addressKey,
        confidence: "Verified match",
        address: {
          address_line_1: "",
          address_line_2: "",
          locality: "",
          region: "",
          postal_code: "",
          country: "US",
        },
      },
    })
  );
};
/**
 * @see https://blog.logrocket.com/using-storybook-and-mock-service-worker-for-mocked-api-responses/
 */
if (typeof global.process === "undefined") {
  const worker = setupWorker(
    rest.get(
      "https://api.experianaperture.io/address/format/v1/:addressKey",
      mockFormatRequest
    ),
    rest.post(
      "https://api.experianaperture.io/address/search/v1",
      mockSearchRequest
    )
  );
  worker.start();
}
