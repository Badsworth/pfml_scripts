import React, { useEffect, useState } from "react";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import usePreviousValue from "../../hooks/usePreviousValue";
import { useTranslation } from "react-i18next";

const EmployeeNotice = ({ fraud, onChange = () => {} }) => {
  const { t } = useTranslation();
  const [employeeNotice, setEmployeeNotice] = useState();
  // keep track of previous value for fraud prop to know when to clear notice of leave response
  const previouslyFraud = usePreviousValue(fraud);

  const handleOnChange = (event) => {
    setEmployeeNotice(event.target.value);
  };

  useEffect(() => {
    onChange(employeeNotice);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employeeNotice]);

  useEffect(() => {
    if (fraud === "Yes" || (fraud === "No" && previouslyFraud === "Yes")) {
      setEmployeeNotice(undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fraud]);

  return (
    <React.Fragment>
      <InputChoiceGroup
        smallLabel
        label={
          <ReviewHeading level="2">
            {t("components.employersEmployeeNotice.heading")}
          </ReviewHeading>
        }
        choices={[
          {
            checked: employeeNotice === "Yes",
            disabled: fraud === "Yes",
            label: t("components.employersEmployeeNotice.choiceYes"),
            value: "Yes",
          },
          {
            checked: employeeNotice === "No",
            disabled: fraud === "Yes",
            label: t("components.employersEmployeeNotice.choiceNo"),
            value: "No",
          },
        ]}
        name="employeeNotice"
        onChange={handleOnChange}
        type="radio"
      />
    </React.Fragment>
  );
};

EmployeeNotice.propTypes = {
  fraud: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

export default EmployeeNotice;
