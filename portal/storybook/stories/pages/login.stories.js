import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import Login from "src/pages/login";
import React from "react";

export default {
  title: "Pages/Auth/Login",
  component: Login,
};

export const Page = (args) => {
  const query = {};
  if (args.query === "Session timed out") {
    query["session-timed-out"] = "true";
  } else if (args.query === "Verified account") {
    query["account-verified"] = "true";
  }

  const appLogic = {
    auth: { login: () => {} },
    appErrors: new AppErrorInfoCollection(),
    portalFlow: { goTo: () => {} },
  };

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
