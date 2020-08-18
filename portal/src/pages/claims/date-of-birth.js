import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.date_of_birth"];

export const DateOfBirth = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const { date_of_birth } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = () =>
    props.appLogic.claims.update(props.claim.application_id, formState, fields);

  return (
    <QuestionPage
      title={t("pages.claimsDateOfBirth.title")}
      onSave={handleSave}
    >
      <InputDate
        name="date_of_birth"
        label={t("pages.claimsDateOfBirth.sectionLabel")}
        hint={t("components.form.dateInputHint")}
        value={valueWithFallback(date_of_birth)}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        onChange={handleInputChange}
      />
    </QuestionPage>
  );
};

DateOfBirth.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(DateOfBirth);
