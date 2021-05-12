import React, { useEffect, useState } from "react";

import BenefitsApplication from "../../models/BenefitsApplication";
import ComboBox from "../../components/ComboBox";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.occupation", "claim.job_title"];

export const AppOccupation = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const showOccupation = isFeatureEnabled("claimantShowOccupation");

  const initialFormState = pick(props, fields).claim;

  if (!showOccupation) {
    // @todo: If the radio buttons are disabled, hard-code the field so that validations pass
  }

  const { formState, updateFields } = useFormState(initialFormState);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const [occupations, setOccupations] = useState([]);

  const populateOccupations = async () => {
    const occupationOptions = await appLogic.benefitsApplications.getOccupations();
    setOccupations(
      occupationOptions.map((occupation) => ({
        label: occupation.occupation_description,
        value: occupation.occupation_description,
      }))
    );
  };

  useEffect(() => {
    populateOccupations();
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
          choices={occupations}
          updateField={(value) => updateFields({ occupation: value })}
          label="Industry"
          smallLabel
        />
        <InputText
          {...getFunctionalInputProps("job_title")}
          label="Job title"
          smallLabel
          maxLength="255"
        />
      </Fieldset>
    </QuestionPage>
  );
};

AppOccupation.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(AppOccupation);
