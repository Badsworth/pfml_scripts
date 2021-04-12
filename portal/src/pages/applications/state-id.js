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
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.has_state_id", "claim.mass_id"];

export const StateId = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );
  const { has_state_id } = formState;

  const handleSave = () => {
    const { mass_id, ...requestData } = { ...formState };
    // API requires any letters in the ID to be uppercase:
    requestData.mass_id = mass_id ? mass_id.toUpperCase() : mass_id;

    appLogic.benefitsApplications.update(claim.application_id, requestData);
  };

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
        clearField={clearField}
        updateFields={updateFields}
        visible={has_state_id === true}
      >
        <InputText
          {...getFunctionalInputProps("mass_id")}
          pii
          label={t("pages.claimsStateId.idLabel")}
          hint={t("pages.claimsStateId.idHint")}
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

export default withBenefitsApplication(StateId);
