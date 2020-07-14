import Claim from "../../models/Claim";
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

export const fields = ["claim.employee_ssn"];

/**
 * A form page to capture the worker's SSN or ITIN.
 */
export const Ssn = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const { employee_ssn } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = () =>
    appLogic.updateClaim(claim.application_id, formState);

  return (
    <QuestionPage title={t("pages.claimsSsn.title")} onSave={handleSave}>
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
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(Ssn);
