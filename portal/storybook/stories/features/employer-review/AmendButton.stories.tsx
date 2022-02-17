/* eslint-disable no-alert */
import AmendButton from "src/features/employer-review/AmendButton";
import React from "react";

export default {
  title: "Features/Employer review/AmendButton",
  component: AmendButton,
};

export const Default = () => {
  return (
    <AmendButton
      onClick={() => alert("This function should open the Amendment Form!")}
    />
  );
};
