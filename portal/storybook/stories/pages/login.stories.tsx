import Login from "src/pages/login";
import { Props } from "types/common";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Login",
  component: Login,
  argTypes: {
    query: {
      control: {
        type: "radio",
        options: ["Default", "Session timed out", "Verified account"],
      },
    },
  },
  args: {
    query: "Default",
  },
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
