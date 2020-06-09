import Claim from "../../models/Claim";
import ClaimsApi from "../../api/ClaimsApi";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import routeWithParams from "../../utils/routeWithParams";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import useHandleSave from "../../hooks/useHandleSave";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

/**
 * A form page to capture a user's attestation of having notified their employer.
 */
export const NotifiedEmployer = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(props.claim);
  const { leave_details } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = useHandleSave(
    (formState) => props.claimsApi.updateClaim(new Claim(formState)),
    (result) => props.updateClaim(result.claim)
  );

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsNotifiedEmployer.title")}
      onSave={handleSave}
      nextPage={routeWithParams("claims.review", props.query)}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: leave_details.employer_notified === true,
            label: t("pages.claimsNotifiedEmployer.choiceYes"),
            value: "true",
          },
          {
            checked: leave_details.employer_notified === false,
            label: t("pages.claimsNotifiedEmployer.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsNotifiedEmployer.sectionLabel")}
        hint={t("pages.claimsNotifiedEmployer.hint")}
        name="leave_details.employer_notified"
        onChange={handleInputChange}
        type="radio"
      />
    </QuestionPage>
  );
};

NotifiedEmployer.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  updateClaim: PropTypes.func,
  claimsApi: PropTypes.instanceOf(ClaimsApi),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(NotifiedEmployer);
