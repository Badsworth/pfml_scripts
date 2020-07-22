import Claim from "../../models/Claim";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import get from "lodash/get";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.temp.leave_details.avg_weekly_hours_worked"];

const AverageWorkHours = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = () =>
    props.appLogic.updateClaim(props.claim.application_id, formState);

  return (
    <QuestionPage
      title={t("pages.claimsAverageWorkHours.title")}
      onSave={handleSave}
    >
      <InputText
        label={t("pages.claimsAverageWorkHours.sectionLabel")}
        name="temp.leave_details.avg_weekly_hours_worked"
        onChange={handleInputChange}
        hint={t("pages.claimsAverageWorkHours.hint")}
        width="small"
        value={valueWithFallback(
          get(formState, "temp.leave_details.avg_weekly_hours_worked")
        )}
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
