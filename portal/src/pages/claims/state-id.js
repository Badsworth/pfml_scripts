import ConditionalContent from "../../components/ConditionalContent";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import User from "../../models/User";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";

const StateId = (props) => {
  const { t } = useTranslation();
  const { user, updateUser } = props.appLogic;
  const { formState, updateFields, removeField } = useFormState(user);
  const { has_state_id, state_id } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  // TODO: Save this field to the appropriate API models once the fields exist
  const handleSave = () =>
    updateUser(user.user_id, new User(formState), props.claim);

  // Note that has_state_id can be null if user has never answered this question before.
  // We should show this field if user already has a state id, and hide it either if
  // indicated that they don't have a state id or if they had never answered the question.
  const shouldShowStateIdField = !!has_state_id;

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsStateId.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: has_state_id === true,
            label: t("pages.claimsStateId.choiceYes"),
            value: "true",
          },
          {
            checked: has_state_id === false,
            label: t("pages.claimsStateId.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsStateId.hasStateIdLabel")}
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
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default StateId;
