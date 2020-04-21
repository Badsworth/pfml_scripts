import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import User from "../../models/User";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import useHandleSave from "../../hooks/useHandleSave";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";

export const DateOfBirth = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(props.user);
  const { dateOfBirth } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  // TODO call API once API module is ready
  // const handleSave = useHandleSave(api.patchUser, props.setUser);
  // For now just save the form state back to the user state directly.
  const handleSave = useHandleSave(
    (formState) => new User(formState),
    props.setUser
  );

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsDateOfBirth.title")}
      onSave={handleSave}
      nextPage={routes.claims.stateId}
    >
      <InputDate
        name="dateOfBirth"
        label={t("pages.claimsDateOfBirth.sectionLabel")}
        value={valueWithFallback(dateOfBirth)}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        onChange={handleInputChange}
      />
    </QuestionPage>
  );
};

DateOfBirth.propTypes = {
  user: PropTypes.instanceOf(User).isRequired,
  setUser: PropTypes.func.isRequired,
};

export default DateOfBirth;
