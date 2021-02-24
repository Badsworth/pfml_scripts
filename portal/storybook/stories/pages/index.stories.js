import Index from "src/pages/index";
import React from "react";

export default {
  title: "Pages/Landing Page",
  component: Index,
};

export const Page = () => {
  const appLogic = {
    portalFlow: { goTo: () => {} },
  };

  return <Index appLogic={appLogic} />;
};
