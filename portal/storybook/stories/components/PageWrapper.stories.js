import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import PageWrapper from "src/components/PageWrapper";
import React from "react";
import User from "src/models/User";

export default {
  title: "Components/PageWrapper",
  component: PageWrapper,
  argTypes: {
    Authentication: {
      defaultValue: "Logged out",
      control: {
        type: "radio",
        options: ["Logged out", "Logged in"],
      },
    },
    Errors: {
      defaultValue: "No errors",
      control: {
        type: "radio",
        options: ["No errors", "Has errors"],
      },
    },
    "Maintenance Page": {
      defaultValue: "Off",
      control: {
        type: "radio",
        options: ["Off", "On"],
      },
    },
  },
};

export const Default = (args) => {
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
      : null;

  const maintenancePageRoutes =
    args["Maintenance Page"] === "On" ? ["/*"] : undefined;
  const pathname = "/storybook-example";

  const appLogic = {
    appErrors: new AppErrorInfoCollection(appErrors),
    auth: {
      logout: () => {},
    },
    portalFlow: {
      pathname,
    },
    users: { user },
  };

  return (
    <PageWrapper
      appLogic={appLogic}
      isLoading={args.isLoading}
      maintenancePageRoutes={maintenancePageRoutes}
    >
      <React.Fragment>
        <h1>Page body</h1>
        <p>This is content wrapped by the PageWrapper component.</p>
      </React.Fragment>
    </PageWrapper>
  );
};
