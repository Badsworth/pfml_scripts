import Claim from "../../models/Claim";
import FormLabel from "../../components/FormLabel";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.first_name",
  // TODO: Uncomment this once validation is in place
  // Disabled as part of the checklist workaround https://lwd.atlassian.net/browse/CP-606
  // See: https://lwd.atlassian.net/browse/CP-625
  // "claim.middle_name",
  "claim.last_name",
];

export const Name = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const { first_name, middle_name, last_name } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = (formState) =>
    props.appLogic.updateClaim(props.claim.application_id, formState);

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsName.title")}
      onSave={handleSave}
    >
      <FormLabel component="legend" hint={t("pages.claimsName.lead")}>
        {t("pages.claimsName.sectionLabel")}
      </FormLabel>
      <InputText
        name="first_name"
        value={valueWithFallback(first_name)}
        label={t("pages.claimsName.firstNameLabel")}
        onChange={handleInputChange}
        smallLabel
      />
      <InputText
        name="middle_name"
        value={valueWithFallback(middle_name)}
        label={t("pages.claimsName.middleNameLabel")}
        optionalText={t("components.form.optionalText")}
        onChange={handleInputChange}
        smallLabel
      />
      <InputText
        name="last_name"
        value={valueWithFallback(last_name)}
        label={t("pages.claimsName.lastNameLabel")}
        onChange={handleInputChange}
        smallLabel
      />
    </QuestionPage>
  );
};

Name.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(Name);
