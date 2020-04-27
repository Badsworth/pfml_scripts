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
  const { has_state_id, state_id } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = useHandleSave(
    (formState) => usersApi.updateUser(new User(formState)),
    (result) => props.setUser(result.user)
  );

  // Note that has_state_id can be null if user has never answered this question before.
  // We should show this field if user already has a state id, and hide it either if
  // indicated that they don't have a state id or if they had never answered the question.
  const shouldShowStateIdField = !!has_state_id;

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
            checked: has_state_id === true,
            label: t("pages.claimsStateId.hasIdChoiceYes"),
            value: "true",
          },
          {
            checked: has_state_id === false,
            label: t("pages.claimsStateId.hasIdChoiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsStateId.hasIdChoiceLabel")}
        name="has_state_id"
        onChange={handleInputChange}
        type="radio"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={["state_id"]}
        removeField={removeField}
        visible={shouldShowStateIdField}
      >
        <InputText
          name="state_id"
          label={t("pages.claimsStateId.idLabel")}
          value={valueWithFallback(state_id)}
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
