import React, { useEffect, useState } from "react";

import BenefitsApplication from "../../models/BenefitsApplication";
import Dropdown from "../../components/Dropdown";
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

export const fields = ["claim.occupation_id", "claim.job_title"];

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

  const occupationDefaults = [
    {
      label: t("pages.claimsOccupation.selectCategory"),
      value: 0,
    },
  ];
  const [occupations, setOccupations] = useState(occupationDefaults);

  const populateOccupations = async () => {
    setOccupations([
      ...occupationDefaults.filter((d) => d.value !== -1),
      ...(await appLogic.benefitsApplications.getOccupations()).map(
        (occupation) => ({
          label: occupation.occupation_description,
          value: occupation.occupation_id,
        })
      ),
    ]);
  };

  useEffect(() => {
    populateOccupations();
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <QuestionPage
      title={t("$t(shared.claimsVerifyIdTitle)")}
      onSave={handleSave}
    >
      <Fieldset>
        <FormLabel
          component="legend"
          hint="This data helps us understand who is accessing our program to ensure it is built for everyone. Your answer will not be shared with your employer."
        >
          What is your current occupation?
        </FormLabel>

        <Dropdown
          {...getFunctionalInputProps(`occupation_id`)}
          choices={occupations}
          label="Industry"
          hideEmptyChoice
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
