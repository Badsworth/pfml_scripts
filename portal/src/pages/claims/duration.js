import Collection from "../../models/Collection";
import ConditionalContent from "../../components/ConditionalContent";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";

const Duration = (props) => {
  const { t } = useTranslation();

  const { claimId } = props.query;
  // TODO remove the `|| {}` fallback
  const claim = props.claims.byId[claimId] || {};
  const { formState, updateFields, removeField } = useFormState(claim);
  const { avgWeeklyHoursWorked, durationType, hoursOffNeeded } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  // TODO call API once API module is ready
  // const handleSave = useHandleSave(api.patchClaim, props.setClaim);
  // TODO save the API result to the claim once we have a `setClaim` function we can use
  // For now just do nothing.
  const handleSave = async () => {};

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsDuration.title")}
      onSave={handleSave}
      // TODO update with correct next route re: pregnancy
      nextPage={routes.home}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: durationType === "continuous",
            label: t("pages.claimsDuration.continuousLabel"),
            hint: t("pages.claimsDuration.continuousHint"),
            value: "continuous",
          },
          {
            checked: durationType === "intermittent",
            hint: t("pages.claimsDuration.intermittentHint"),
            label: t("pages.claimsDuration.intermittentLabel"),
            value: "intermittent",
          },
        ]}
        label={t("pages.claimsDuration.sectionLabel")}
        name="durationType"
        onChange={handleInputChange}
        type="radio"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={["avgWeeklyHoursWorked", "hoursOffNeeded"]}
        removeField={removeField}
        visible={durationType === "intermittent"}
      >
        <InputText
          label={t("pages.claimsDuration.avgWeeklyHoursWorkedLabel")}
          hint={t("pages.claimsDuration.avgWeeklyHoursWorkedHint")}
          name="avgWeeklyHoursWorked"
          value={valueWithFallback(avgWeeklyHoursWorked)}
          onChange={handleInputChange}
          width="small"
        />
        <InputText
          label={t("pages.claimsDuration.hoursOffNeededLabel")}
          hint={t("pages.claimsDuration.hoursOffNeededHint")}
          name="hoursOffNeeded"
          value={valueWithFallback(hoursOffNeeded)}
          onChange={handleInputChange}
          width="small"
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

Duration.propTypes = {
  claims: PropTypes.instanceOf(Collection).isRequired,
  query: PropTypes.shape({
    claimId: PropTypes.string,
  }),
};

export default Duration;
