import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import Login from "src/pages/login";
import { Props } from "storybook/types";
import React from "react";

export default {
  title: "Pages/Auth/Login",
  component: Login,
};

export const Page = (args: Props<typeof Login>) => {
  const query = {};
  if (args.query === "Session timed out") {
    // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    query["session-timed-out"] = "true";
  } else if (args.query === "Verified account") {
    // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    query["account-verified"] = "true";
  }

  const appLogic = {
    auth: { login: () => {} },
    appErrors: new AppErrorInfoCollection(),
    portalFlow: { goTo: () => {} },
  };

  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ auth: { login: () => void; }; appErrors: A... Remove this comment to see the full error message
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
