import Flag from "src/models/Flag";
import PageWrapper from "src/components/PageWrapper";
import { Props } from "types/common";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Templates/Page wrapper",
  component: PageWrapper,
  argTypes: {
    Authentication: {
      control: {
        type: "radio",
        options: ["Logged out", "Logged in"],
      },
    },
    Errors: {
      control: {
        type: "radio",
        options: ["No errors", "Has errors"],
      },
    },
    "Maintenance Page": {
      control: {
        type: "radio",
        options: ["Off", "On"],
      },
    },
  },
  args: {
    Authentication: "Logged out",
    Errors: "No errors",
    "Maintenance Page": "Off",
  },
};

export const Default = (
  args: Props<typeof PageWrapper> & {
    Authentication: string;
    Errors: string;
    "Maintenance Page": string;
  }
) => {
  const errors =
    args.Errors === "Has errors"
      ? [new Error("This is a Storybook error message example.")]
      : [];

  const user =
    args.Authentication === "Logged in"
      ? new User({ email_address: "test@example.com" })
      : undefined;

  const maintenance = new Flag({
    name: "maintenance",
    enabled: args["Maintenance Page"] === "On",
    options: {
      page_routes: args["Maintenance Page"] === "On" ? ["/*"] : [],
    },
  });

  const appLogic = useMockableAppLogic({
    errors,
    users: { user },
  });

  return (
    <PageWrapper
      appLogic={appLogic}
      isLoading={args.isLoading}
      maintenance={maintenance}
    >
      <React.Fragment>
        <h1>Page body</h1>
        <p>This is content wrapped by the PageWrapper component.</p>
      </React.Fragment>
    </PageWrapper>
  );
};
