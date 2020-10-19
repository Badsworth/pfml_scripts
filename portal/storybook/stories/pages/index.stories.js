import { Index } from "src/pages/index";
import React from "react";
import routes from "src/routes";

export default {
  title: "Pages/Claimant dashboard",
  component: Index,
};

export const Page = () => (
  <Index
    appLogic={{
      portalFlow: {
        pathname: routes.home,
      },
    }}
  />
);
