import Claim from "../../models/Claim";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.temp.leave_details.avg_weekly_work_hours"];

// TODO (CP-1034): Add page back into the flow and connect fields to the API
export const AverageWorkHours = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsAverageWorkHours.title")}
      onSave={handleSave}
    >
      <InputText
        {...getFunctionalInputProps("temp.leave_details.avg_weekly_work_hours")}
        label={t("pages.claimsAverageWorkHours.sectionLabel")}
        hint={t("pages.claimsAverageWorkHours.hint")}
        width="small"
      />
    </QuestionPage>
  );
};

AverageWorkHours.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(AverageWorkHours);
