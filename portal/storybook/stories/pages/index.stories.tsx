import Index from "src/pages/index";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Landing Page",
  component: Index,
};

export const DefaultStory = () => {
  const appLogic = useMockableAppLogic();

  return <Index appLogic={appLogic} />;
};
