/* eslint-disable no-alert */
import AmendButton from "src/components/employers/AmendButton";
import React from "react";

export default {
  title: "Components/AmendButton",
  component: AmendButton,
};

export const Default = () => {
  return (
    <AmendButton
      onClick={() => alert("This function should open the Amendment Form!")}
    />
  );
};
