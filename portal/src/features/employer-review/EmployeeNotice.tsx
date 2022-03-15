import React, { useEffect } from "react";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import ReviewHeading from "../../components/ReviewHeading";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import usePreviousValue from "../../hooks/usePreviousValue";
import { useTranslation } from "react-i18next";

interface EmployeeNoticeProps {
  employeeNoticeInput?: "Yes" | "No";
  fraudInput?: string;
  getFunctionalInputProps: ReturnType<typeof useFunctionalInputProps>;
  updateFields: (fields: { [fieldName: string]: unknown }) => void;
}

const EmployeeNotice = ({
  employeeNoticeInput,
  fraudInput,
  getFunctionalInputProps,
  updateFields,
}: EmployeeNoticeProps) => {
  const { t } = useTranslation();
  // keep track of previous value for fraud prop to know when to clear notice of leave response
  const previouslyFraud = usePreviousValue(fraudInput);

  useEffect(() => {
    if (
      fraudInput === "Yes" ||
      (fraudInput === "No" && previouslyFraud === "Yes")
    ) {
      updateFields({ employee_notice: undefined });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fraudInput]);

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps("employee_notice")}
        smallLabel
        label={
          <ReviewHeading level="2">
            {t("components.employersEmployeeNotice.heading")}
          </ReviewHeading>
        }
        choices={[
          {
            checked: employeeNoticeInput === "Yes",
            disabled: fraudInput === "Yes",
            label: t("components.employersEmployeeNotice.choiceYes"),
            value: "Yes",
          },
          {
            checked: employeeNoticeInput === "No",
            disabled: fraudInput === "Yes",
            label: t("components.employersEmployeeNotice.choiceNo"),
            value: "No",
          },
        ]}
        type="radio"
      />
    </React.Fragment>
  );
};

export default EmployeeNotice;
