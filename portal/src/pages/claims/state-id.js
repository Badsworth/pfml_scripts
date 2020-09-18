import ConditionalContent from "../../components/ConditionalContent";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.has_state_id", "claim.mass_id"];

export const StateId = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, removeField } = useFormState(
    pick(props, fields).claim
  );
  const { has_state_id } = formState;

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage title={t("pages.claimsStateId.title")} onSave={handleSave}>
      <InputChoiceGroup
        {...getFunctionalInputProps("has_state_id")}
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
          {...getFunctionalInputProps("mass_id")}
          clearInitialPii
          label={t("pages.claimsStateId.idLabel")}
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
