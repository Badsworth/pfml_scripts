import FormLabel from "../../components/FormLabel";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import User from "../../models/User";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import useHandleSave from "../../hooks/useHandleSave";
import { useTranslation } from "../../locales/i18n";
import usersApi from "../../api/usersApi";
import valueWithFallback from "../../utils/valueWithFallback";

const Name = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(props.user);
  const { firstName, middleName, lastName } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = useHandleSave(
    (formState) => usersApi.updateUser(new User(formState)),
    (result) => props.setUser(result.user)
  );

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsName.title")}
      onSave={handleSave}
      nextPage={routes.claims.dateOfBirth}
    >
      <FormLabel
        component="legend"
        hint={t("pages.claimsName.nameSectionHint")}
      >
        {t("pages.claimsName.sectionLabel")}
      </FormLabel>
      <InputText
        name="firstName"
        value={valueWithFallback(firstName)}
        label={t("pages.claimsName.firstNameLabel")}
        onChange={handleInputChange}
        smallLabel
      />
      <InputText
        name="middleName"
        value={valueWithFallback(middleName)}
        label={t("pages.claimsName.middleNameLabel")}
        optionalText={t("components.form.optionalText")}
        onChange={handleInputChange}
        smallLabel
      />
      <InputText
        name="lastName"
        value={valueWithFallback(lastName)}
        label={t("pages.claimsName.lastNameLabel")}
        onChange={handleInputChange}
        smallLabel
      />
    </QuestionPage>
  );
};

Name.propTypes = {
  user: PropTypes.instanceOf(User).isRequired,
  setUser: PropTypes.func.isRequired,
};

export default Name;
