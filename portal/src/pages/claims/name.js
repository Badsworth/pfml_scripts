import Claim from "../../models/Claim";
import ClaimsApi from "../../api/ClaimsApi";
import FormLabel from "../../components/FormLabel";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import routeWithParams from "../../utils/routeWithParams";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import useHandleSave from "../../hooks/useHandleSave";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = ["first_name", "middle_name", "last_name"];

export const Name = (props) => {
  const { claim, claimsApi, updateClaim } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(claim, fields));
  const { first_name, middle_name, last_name } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = useHandleSave(
    (formState) => claimsApi.updateClaim(claim.application_id, formState),
    (result) => updateClaim(result.claim)
  );

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsName.title")}
      onSave={handleSave}
      nextPage={routeWithParams("claims.dateOfBirth", props.query)}
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
  claimsApi: PropTypes.instanceOf(ClaimsApi),
  updateClaim: PropTypes.func.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(Name);
