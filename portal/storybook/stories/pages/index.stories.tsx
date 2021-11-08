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

  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ appErrors: { items: never[]; }; documents:... Remove this comment to see the full error message
  return <Index appLogic={appLogic} />;
};
