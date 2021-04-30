import BenefitsApplication from "../../models/BenefitsApplication";
// import Occupation, { OccupationTitle } from "../../models/Occupation";
// import Alert from "../../components/Alert";
// import ConditionalContent from "../../components/ConditionalContent";
// import Details from "../../components/Details";
// import InputChoiceGroup from "../../components/InputChoiceGroup";
// import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
// import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
// import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.occupation_id", "claim.occupation_title_id"];

export const AppOccupation = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const showOccupation = isFeatureEnabled("claimantShowOccupation");

  const initialFormState = pick(props, fields).claim;

  if (!showOccupation) {
    // @todo: If the radio buttons are disabled, hard-code the field so that validations pass
  }

  const { formState /* getField, updateFields, clearField */ } = useFormState(
    initialFormState
  );
  // const occupation_id = get(formState, "occupation_id");
  // const occupation_title_id = get(formState, "occupation_title_id");

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  /* const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  }); */
  const occupations = [];
  return (
    <QuestionPage title={t("pages.claimsOccupation.title")} onSave={handleSave}>
      <p>hi</p>
      <select name="yep" id="yep">
        {occupations.length &&
          occupations.map((o) => (
            <option key={o.occupation_id} value={o.occupation_id}>
              {o.occupation_description}
            </option>
          ))}
      </select>
    </QuestionPage>
  );
};

AppOccupation.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(AppOccupation);
