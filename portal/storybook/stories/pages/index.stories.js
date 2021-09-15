import Index from "src/pages/index";
import React from "react";

export default {
  title: "Pages/Landing Page",
  component: Index,
};

export const DefaultStory = () => {
  const appLogic = {
    appErrors: { items: [] },
    documents: { download: () => {} },
    portalFlow: {
      getNextPageRoute: () => "/storybook-mock",
      goTo: () => {},
    },
  };

  return <Index appLogic={appLogic} />;
};
