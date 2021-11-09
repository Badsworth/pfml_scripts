import Router, { NextRouter } from "next/router";
import React from "react";
import { RouterContext } from "next/dist/shared/lib/router-context";
import { mockRouter } from "lib/mock-helpers/router";

const Provider = RouterContext.Provider;
Router.router = mockRouter;

export const WithNextRouter = (Story: React.FC<unknown>): JSX.Element => {
  return (
    <Provider value={Router.router as NextRouter}>
      <Story />
    </Provider>
  );
};
