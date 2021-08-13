import React from "react";
import { Status } from "src/pages/applications/status";

export default {
  title: `Pages/Applications/Status`,
  component: Status,
};

export const DefaultStory = () => {
  const appLogic = {
    portalFlow: {
      getNextPageRoute: () => "/storybook-mock",
    },
  };
  return <Status appLogic={appLogic} />;
};
