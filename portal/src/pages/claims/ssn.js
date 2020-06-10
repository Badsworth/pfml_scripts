import Claim from "../../models/Claim";
import ClaimsApi from "../../api/ClaimsApi";
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

export const fields = ["employee_ssn"];

/**
 * A form page to capture the worker's SSN or ITIN.
 */
export const Ssn = (props) => {
  const { claim, claimsApi, query, updateClaim } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(claim, fields));
  const { employee_ssn } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = useHandleSave(
    (formState) => claimsApi.updateClaim(claim.application_id, formState),
    (result) => updateClaim(result.claim)
  );

  const nextPage = routeWithParams("claims.leaveReason", query);

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsSsn.title")}
      onSave={handleSave}
      nextPage={nextPage}
    >
      <InputText
        mask="ssn"
        name="employee_ssn"
        value={valueWithFallback(employee_ssn)}
        label={t("pages.claimsSsn.sectionLabel")}
        hint={t("pages.claimsSsn.lead")}
        onChange={handleInputChange}
      />
    </QuestionPage>
  );
};

Ssn.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  claimsApi: PropTypes.instanceOf(ClaimsApi),
  updateClaim: PropTypes.func.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(Ssn);
