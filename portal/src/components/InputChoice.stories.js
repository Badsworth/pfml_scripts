import InputChoice from "./InputChoice";
import React from "react";

export default {
  title: "Forms|InputChoice",
  component: InputChoice
};

export const Default = () => {
  return (
    <form className="usa-form">
      <h2>Checkbox (default)</h2>
      <InputChoice
        label="Checkbox field"
        name="checkboxFieldName"
        value="yes"
      />

      <h2>Radio</h2>
      <InputChoice
        hint="Example of a radio field with hint text."
        label="Yes"
        name="radioFieldName"
        type="radio"
        value="yes"
      />
      <InputChoice label="No" name="radioFieldName" type="radio" value="no" />
    </form>
  );
};
