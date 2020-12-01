import React, { useEffect, useRef, useState } from "react";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import { useTranslation } from "react-i18next";

const EmployeeNotice = ({ fraud, onChange = () => {} }) => {
  const { t } = useTranslation();
  const [employeeNotice, setEmployeeNotice] = useState();
  // keep track of previous value for fraud prop to know when to clear notice of leave response
  const prevFraud = useRef(false);

  const handleOnChange = (event) => {
    setEmployeeNotice(event.target.value);
  };

  useEffect(() => {
    onChange(employeeNotice);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employeeNotice]);

  useEffect(() => {
    if (fraud === "Yes" || (fraud === "No" && prevFraud.current)) {
      setEmployeeNotice(undefined);
    }
    prevFraud.current = fraud;
  }, [fraud]);

  return (
    <React.Fragment>
      <InputChoiceGroup
        label={
          <ReviewHeading level="2">
            {t("pages.employersClaimsReview.employeeNotice.heading")}
          </ReviewHeading>
        }
        choices={[
          {
            checked: employeeNotice === "Yes",
            disabled: fraud === "Yes",
            label: t("pages.employersClaimsReview.employeeNotice.choiceYes"),
            value: "Yes",
          },
          {
            checked: employeeNotice === "No",
            disabled: fraud === "Yes",
            label: t("pages.employersClaimsReview.employeeNotice.choiceNo"),
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
