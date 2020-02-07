import { object as objectKnob, withKnobs } from "@storybook/addon-knobs";
import AuthNav from "./AuthNav";
import React from "react";

export default {
  title: "AuthNav",
  component: AuthNav,
  decorators: [withKnobs]
};

export const WithUser = () => {
  const defaultUser = { username: "Bud Baxter" };
  const user = objectKnob("user", defaultUser);

  return <AuthNav user={user} />;
};
