import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import Flag from "src/models/Flag";
import PageWrapper from "src/components/PageWrapper";
import { Props } from "types/common";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Components/PageWrapper",
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
  const appErrors =
    args.Errors === "Has errors"
      ? [
          new AppErrorInfo({
            message: "This is a Storybook error message example.",
          }),
        ]
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
    appErrors: new AppErrorInfoCollection(appErrors),
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