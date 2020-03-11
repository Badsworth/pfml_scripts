import React, { useState } from "react";
import InputChoiceGroup from "./InputChoiceGroup";
import PropType from "prop-types";
import Title from "./Title";
import WagesTable from "./WagesTable";
import { useTranslation } from "react-i18next";

/**
 * A view that is conditionally rendered on the Result page when the claimant is eligible.
 */
const Eligible = props => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    dataIsCorrect: null,
  });

  const handleChange = event => {
    const { name, value } = event.target;
    setFormData({ ...formData, [name]: value });
  };

  return (
    <React.Fragment>
      <Title>{t("components.eligible.title")}</Title>
      <WagesTable employeeId={props.employeeId} eligibility="eligible" />

      <form className="usa-form usa-form--large margin-y-6">
        <InputChoiceGroup
          label={t("components.eligible.dataIsCorrectLabel")}
          type="radio"
          name="dataIsCorrect"
          onChange={handleChange}
          choices={[
            {
              checked: formData.dataIsCorrect === "yes",
              label: "Yes",
              value: "yes",
            },
            {
              checked: formData.dataIsCorrect === "no",
              label: "No",
              value: "no",
            },
          ]}
        />
      </form>
    </React.Fragment>
  );
};

Eligible.propTypes = {
  /**
   * Id for employee whose result will be displayed
   */
  employeeId: PropType.string.isRequired,
};

export default Eligible;
