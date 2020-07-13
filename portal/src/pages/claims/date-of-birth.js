import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import User from "../../models/User";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const DateOfBirth = (props) => {
  const { t } = useTranslation();
  const { user, updateUser } = props.appLogic;
  const { formState, updateFields } = useFormState(user);
  const { date_of_birth } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  // TODO: Save this field to the appropriate API models once the fields exist
  const handleSave = () =>
    updateUser(user.user_id, new User(formState), props.claim);

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsDateOfBirth.title")}
      onSave={handleSave}
    >
      <InputDate
        name="date_of_birth"
        label={t("pages.claimsDateOfBirth.sectionLabel")}
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
