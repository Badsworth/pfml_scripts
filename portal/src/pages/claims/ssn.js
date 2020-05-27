import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import User from "../../models/User";
import { isFeatureEnabled } from "../../services/featureFlags";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import useHandleSave from "../../hooks/useHandleSave";
import { useTranslation } from "../../locales/i18n";
import usersApi from "../../api/usersApi";
import valueWithFallback from "../../utils/valueWithFallback";

/**
 * A form page to capture the worker's SSN or ITIN.
 */
const Ssn = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(props.user);
  const { ssn_or_itin } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = useHandleSave(
    (formState) => usersApi.updateUser(new User(formState)),
    (result) => props.setUser(result.user)
  );

  const nextPage = isFeatureEnabled("unrestrictedClaimFlow")
    ? routeWithParams("claims.leaveType", props.query)
    : routes.claims.success;

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsSsn.title")}
      onSave={handleSave}
      nextPage={nextPage}
    >
      <InputText
        mask="ssn"
        name="ssn_or_itin"
        value={valueWithFallback(ssn_or_itin)}
        label={t("pages.claimsSsn.sectionLabel")}
        hint={t("pages.claimsSsn.lead")}
        onChange={handleInputChange}
      />
    </QuestionPage>
  );
};

Ssn.propTypes = {
  user: PropTypes.instanceOf(User).isRequired,
  setUser: PropTypes.func.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default Ssn;
