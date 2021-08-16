import React from "react";
import { Status } from "src/pages/applications/status";

export default {
  title: `Pages/Applications/Status`,
  component: Status,
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
  return <Status appLogic={appLogic} />;
};
