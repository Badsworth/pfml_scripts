import Occupation, { OccupationTitle } from "../../models/Occupation";

import BenefitsApplication from "../../models/BenefitsApplication";
import Dropdown from "../../components/Dropdown";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [
  "claim.occupation_id",
  "claim.occupation_title_id",
  "claim.occupation_title_custom",
];

export const AppOccupation = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const showOccupation = isFeatureEnabled("claimantShowOccupation");

  const initialFormState = pick(props, fields).claim;

  if (!showOccupation) {
    // @todo: If the radio buttons are disabled, hard-code the field so that validations pass
  }

  const { formState, getField, updateFields /* , clearField */ } = useFormState(
    initialFormState
  );
  const occupation_id = getField("occupation_id");
  /*   const occupation_title_id = getField("occupation_title_id");
  const occupation_title_custom = getField("occupation_title_custom"); */

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });
  const occupations = [
    {
      label: "Select an industry category",
      value: 0,
    },
    {
      label: "Cat1",
      value: 1,
    },
    {
      label: "Other",
      value: -1,
    },
  ];
  const occupation_titles = [];
  // console.log("current occupation_id", occupation_id, occupation_id !== -1)
  return (
    <QuestionPage title={t("pages.claimsOccupation.title")} onSave={handleSave}>
      <Dropdown
        {...getFunctionalInputProps(`occupation_id`)}
        choices={occupations}
        label="Occupation"
        labelClassName="text-normal margin-top-0"
        formGroupClassName="margin-top-1"
        hideEmptyChoice
        smallLabel
      />
      <Dropdown
        {...getFunctionalInputProps(`occupation_title_id`)}
        choices={occupation_titles}
        label="Occupation Title"
        labelClassName="text-normal margin-top-0"
        formGroupClassName="margin-top-1"
        hideEmptyChoice
        smallLabel
        disabled={parseInt(occupation_id) < 1}
      />
      <InputText
        {...getFunctionalInputProps("occupation_title_custom")}
        label="Custom occupation title"
        smallLabel
        disabled={parseInt(occupation_id) !== -1}
      />
    </QuestionPage>
  );
};

AppOccupation.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(AppOccupation);
