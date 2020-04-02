import "@aws-amplify/ui/dist/style.css";
import { Auth } from "aws-amplify";
import Authenticator from "./Authenticator";
import React from "react";

export default {
  title: "Global|Authenticator",
  component: Authenticator,
};

const handleSignOut = () => {
  Auth.signOut();
};

export const WithUser = () => (
  <Authenticator>
    <h1>You are signed in!</h1>
    <button onClick={handleSignOut}>Sign out!</button>
  </Authenticator>
);
