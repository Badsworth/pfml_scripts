import ConditionalContent from "../../components/ConditionalContent";
import InputChoiceGroup from "../../components/InputChoiceGroup";
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

const StateId = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields, removeField } = useFormState(props.user);
  const { hasStateId, stateId } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = useHandleSave(
    (formState) => usersApi.updateUser(new User(formState)),
    (result) => props.setUser(result.user)
  );

  // Note that hasStateId can be null if user has never answered this question before.
  // We should show this field if user already has a state id, and hide it either if
  // indicated that they don't have a state id or if they had never answered the question.
  const shouldShowStateIdField = !!hasStateId;

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsStateId.title")}
      onSave={handleSave}
      nextPage={routes.claims.ssn}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: hasStateId === true,
            label: t("pages.claimsStateId.hasIdChoiceYes"),
            value: "true",
          },
          {
            checked: hasStateId === false,
            label: t("pages.claimsStateId.hasIdChoiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsStateId.hasIdChoiceLabel")}
        name="hasStateId"
        onChange={handleInputChange}
        type="radio"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={["stateId"]}
        removeField={removeField}
        visible={shouldShowStateIdField}
      >
        <InputText
          name="stateId"
          label={t("pages.claimsStateId.idLabel")}
          value={valueWithFallback(stateId)}
          onChange={handleInputChange}
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

StateId.propTypes = {
  user: PropTypes.instanceOf(User).isRequired,
  setUser: PropTypes.func.isRequired,
};

export default StateId;
