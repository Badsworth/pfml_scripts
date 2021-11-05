/* eslint-disable no-alert */
import React, { useState } from "react";
import AmendmentForm from "src/components/employers/AmendmentForm";
import InputDate from "src/components/InputDate";

export default {
  title: "Components/AmendmentForm",
  component: AmendmentForm,
};

export const Default = () => {
  const [value, setFieldValue] = useState("2020-01-01");
  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'evt' implicitly has an 'any' type.
  const handleOnChange = (evt) => {
    setFieldValue(evt.target.value);
  };

  return (
    <AmendmentForm
      // @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: Element; onCancel: () => void; }... Remove this comment to see the full error message
      onCancel={() => alert("This function should hide and clear the form!")}
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
