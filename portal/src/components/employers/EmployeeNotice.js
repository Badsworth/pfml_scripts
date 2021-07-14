import React, { useEffect } from "react";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import usePreviousValue from "../../hooks/usePreviousValue";
import { useTranslation } from "react-i18next";

const EmployeeNotice = (props) => {
  const { t } = useTranslation();
  // keep track of previous value for fraud prop to know when to clear notice of leave response
  const previouslyFraud = usePreviousValue(props.fraudInput);

  useEffect(() => {
    if (
      props.fraudInput === "Yes" ||
      (props.fraudInput === "No" && previouslyFraud === "Yes")
    ) {
      props.updateFields({ employee_notice: undefined });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.fraudInput]);

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...props.getFunctionalInputProps("employee_notice")}
        smallLabel
        label={
          <ReviewHeading level="2">
            {t("components.employersEmployeeNotice.heading")}
          </ReviewHeading>
        }
        choices={[
          {
            checked: props.employeeNoticeInput === "Yes",
            disabled: props.fraudInput === "Yes",
            label: t("components.employersEmployeeNotice.choiceYes"),
            value: "Yes",
          },
          {
            checked: props.employeeNoticeInput === "No",
            disabled: props.fraudInput === "Yes",
            label: t("components.employersEmployeeNotice.choiceNo"),
            value: "No",
          },
        ]}
        type="radio"
      />
    </React.Fragment>
  );
};

EmployeeNotice.propTypes = {
  employeeNoticeInput: PropTypes.oneOf(["Yes", "No"]),
  fraudInput: PropTypes.string,
  getFunctionalInputProps: PropTypes.func.isRequired,
  updateFields: PropTypes.func.isRequired,
};

export default EmployeeNotice;
