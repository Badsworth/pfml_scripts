import { object as objectKnob, withKnobs } from "@storybook/addon-knobs";
import Header from "./Header";
import React from "react";

export default {
  title: "Header",
  component: Header,
  decorators: [withKnobs]
};

export const WithUser = () => {
  const defaultUser = { username: "Bud Baxter" };
  const user = objectKnob("user", defaultUser);

  return <Header user={user} />;
};
