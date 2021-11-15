import Login from "src/pages/login";
import { Props } from "storybook/types";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Login",
  component: Login,
};

export const Page = (args: Props<typeof Login>) => {
  const query: { [key: string]: string } = {};
  if (args.query === "Session timed out") {
    query["session-timed-out"] = "true";
  } else if (args.query === "Verified account") {
    query["account-verified"] = "true";
  }

  const appLogic = useMockableAppLogic();

  return <Login appLogic={appLogic} query={query} />;
};

Page.argTypes = {
  query: {
    defaultValue: "Default",
    control: {
      type: "radio",
      options: ["Default", "Session timed out", "Verified account"],
    },
  },
};
