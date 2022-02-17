/* eslint-disable no-alert */
import React, { useState } from "react";
import AmendmentForm from "src/components/AmendmentForm";
import InputDate from "src/components/core/InputDate";

export default {
  title: "Components/AmendmentForm",
  component: AmendmentForm,
};

export const Default = () => {
  const [value, setFieldValue] = useState("2020-01-01");

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
    setFieldValue(evt.target.value);
  };

  return (
    <AmendmentForm
      destroyButtonLabel="Cancel"
      onDestroy={() => alert("This function should hide and clear the form!")}
    >
      <InputDate
        onChange={handleOnChange}
        value={value}
        label="When did the employee give notice?"
        name="employer-notification-date-amendment"
        dayLabel="Day"
        monthLabel="Month"
        yearLabel="Year"
        smallLabel
      />
    </AmendmentForm>
  );
};
