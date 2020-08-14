import ConditionalContent from "../../components/ConditionalContent";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.has_state_id", "claim.mass_id"];

const StateId = (props) => {
  const { t } = useTranslation();
  const { formState, getField, updateFields, removeField } = useFormState(
    pick(props, fields).claim
  );
  const { has_state_id, mass_id } = formState;
  const handleInputChange = useHandleInputChange(updateFields);
  const handleSave = () =>
    props.appLogic.claims.update(props.claim.application_id, formState);

  return (
    <QuestionPage title={t("pages.claimsStateId.title")} onSave={handleSave}>
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
        fieldNamesClearedWhenHidden={["mass_id"]}
        getField={getField}
        removeField={removeField}
        updateFields={updateFields}
        visible={has_state_id === true}
      >
        <InputText
          name="mass_id"
          label={t("pages.claimsStateId.idLabel")}
          value={valueWithFallback(mass_id)}
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

export default withClaim(StateId);
