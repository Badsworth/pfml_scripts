import { removeField, updateFieldFromEvent } from "../../actions";
import ConditionalContent from "../../components/ConditionalContent";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { connect } from "react-redux";
import routes from "../../routes";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";

export const Duration = (props) => {
  const { t } = useTranslation();
  const { avgWeeklyHoursWorked, durationType, hoursOffNeeded } = props.formData;

  return (
    <QuestionPage
      title={t("pages.claimsDuration.title")}
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
        onChange={props.updateFieldFromEvent}
        type="radio"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={["avgWeeklyHoursWorked", "hoursOffNeeded"]}
        removeField={props.removeField}
        visible={durationType === "intermittent"}
      >
        <InputText
          label={t("pages.claimsDuration.avgWeeklyHoursWorkedLabel")}
          hint={t("pages.claimsDuration.avgWeeklyHoursWorkedHint")}
          name="avgWeeklyHoursWorked"
          value={valueWithFallback(avgWeeklyHoursWorked)}
          onChange={props.updateFieldFromEvent}
          width="small"
        />
        <InputText
          label={t("pages.claimsDuration.hoursOffNeededLabel")}
          hint={t("pages.claimsDuration.hoursOffNeededHint")}
          name="hoursOffNeeded"
          value={valueWithFallback(hoursOffNeeded)}
          onChange={props.updateFieldFromEvent}
          width="small"
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

Duration.propTypes = {
  formData: PropTypes.shape({
    avgWeeklyHoursWorked: PropTypes.string,
    durationType: PropTypes.string,
    hoursOffNeeded: PropTypes.string,
  }).isRequired,
  removeField: PropTypes.func.isRequired,
  updateFieldFromEvent: PropTypes.func.isRequired,
};

const mapStateToProps = (state) => ({
  formData: state.form,
});

const mapDispatchToProps = { updateFieldFromEvent, removeField };

export default connect(mapStateToProps, mapDispatchToProps)(Duration);
