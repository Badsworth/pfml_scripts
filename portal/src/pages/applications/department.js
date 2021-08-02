import React, { useEffect, useState } from "react";

import BenefitsApplication from "../../models/BenefitsApplication";
import ComboBox from "../../components/ComboBox";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
// import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.org_unit"];

export const Department = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  // const showDepartments = isFeatureEnabled("claimantShowDepartments");

  const initialFormState = pick(props, fields).claim;

  // if (!showDepartments) {
  //   // @todo: If the radio buttons are disabled, hard-code the field so that validations pass
  // }

  const { formState, updateFields } = useFormState(initialFormState);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const [departments, setDepartments] = useState([]);

  const populateDepartments = () => {
    // const occupationOptions = await appLogic.benefitsApplications.getDepartments();
    const departmentOptions = [
      { department_description: "HR" },
      { department_description: "DFML" },
      { department_description: "Contact Center" },
      { department_description: "DevOps" },
    ];
    setDepartments(
      departmentOptions.map((department) => ({
        label: department.department_description,
        value: department.department_description,
      }))
    );
  };

  useEffect(() => {
    populateDepartments();
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <Fieldset>
        <FormLabel
          component="legend"
          hint="This data helps us understand who is accessing our program to ensure it is built for everyone. Your answer will not be shared with your employer."
        >
          What is your current occupation?
        </FormLabel>

        <ComboBox
          {...getFunctionalInputProps("occupation")}
          choices={departments}
          updateField={(value) => updateFields({ occupation: value })}
          emptyChoiceLabel="No matches"
          label="Department"
          smallLabel
        />
      </Fieldset>
    </QuestionPage>
  );
};

Department.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(Department);
