import Claim, {
  ContinuousLeavePeriod,
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
  ReducedScheduleLeavePeriod,
} from "../../models/Claim";
import { get, pick } from "lodash";
import ConditionalContent from "../../components/ConditionalContent";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.temp.leave_details.continuous_leave_periods[0]",
  "claim.temp.leave_details.reduced_schedule_leave_periods[0]",
  "claim.leave_details.intermittent_leave_periods[0]",
];

export const every6monthsId = "every6months";

const Duration = (props) => {
  const { t } = useTranslation();
  const { formState, getField, updateFields, removeField } = useFormState({
    ...pick(props, fields).claim,
    duration_type_continuous: props.claim.isContinuous,
    duration_type_reduced: props.claim.isReducedSchedule,
    duration_type_intermittent: props.claim.isIntermittent,
  });

  const {
    duration_type_continuous,
    duration_type_intermittent,
    duration_type_reduced,
  } = formState;
  const continuousLeavePeriod = new ContinuousLeavePeriod(
    get(formState, "temp.leave_details.continuous_leave_periods[0]")
  );
  const reducedScheduleLeavePeriod = new ReducedScheduleLeavePeriod(
    get(formState, "temp.leave_details.reduced_schedule_leave_periods[0]")
  );
  const intermittentLeavePeriod = new IntermittentLeavePeriod(
    get(formState, "leave_details.intermittent_leave_periods[0]")
  );

  const handleInputChange = useHandleInputChange(updateFields);

  // The radio input for intermittentLeavePeriod.frequency_interval_basis
  // actually captures both frequency_interval_basis and frequency_interval
  // data. e.g Twice (frequency) every 6 (frequency interval) months (frequency interval basis)
  // This callback determines whether the frequency interval should be set
  // by the id of the choice input.
  const handleFrequencyBasisChange = (event) => {
    const frequency_interval = event.target.id === every6monthsId ? 6 : null;
    updateFields({
      "leave_details.intermittent_leave_periods[0].frequency_interval": frequency_interval,
    });
    handleInputChange(event);
  };

  const handleSave = () => {
    const {
      duration_type_continuous,
      duration_type_intermittent,
      duration_type_reduced,
      ...patchData
    } = formState;
    props.appLogic.claims.update(props.claim.application_id, patchData, fields);
  };

  return (
    <QuestionPage title={t("pages.claimsDuration.title")} onSave={handleSave}>
      <InputChoiceGroup
        choices={[
          {
            checked: duration_type_continuous,
            label: t("pages.claimsDuration.continuousTypeLabel"),
            hint: t("pages.claimsDuration.continuousTypeHint"),
            name: "duration_type_continuous",
            value: "true",
            key: "continuous",
          },
          {
            checked: duration_type_reduced,
            label: t("pages.claimsDuration.reducedTypeLabel"),
            hint: t("pages.claimsDuration.reducedTypeHint"),
            name: "duration_type_reduced",
            value: "true",
            key: "reduced",
          },
          {
            checked: duration_type_intermittent,
            hint: t("pages.claimsDuration.intermittentTypeHint"),
            label: t("pages.claimsDuration.intermittentTypeLabel"),
            name: "duration_type_intermittent",
            value: "true",
            key: "intermittent",
          },
        ]}
        label={t("pages.claimsDuration.durationTypeSectionLabel")}
        hint={
          <React.Fragment>
            <p>{t("pages.claimsDuration.durationTypeSectionHint")}</p>
            <p>{t("pages.claimsDuration.durationTypeSelectAllHint")}</p>
          </React.Fragment>
        }
        name="duration_type"
        onChange={handleInputChange}
        type="checkbox"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "temp.leave_details.continuous_leave_periods[0]",
        ]}
        getField={getField}
        updateFields={updateFields}
        removeField={removeField}
        visible={duration_type_continuous}
        name="continuous_section"
      >
        <InputText
          inputMode="numeric"
          pattern="[0-9]*"
          label={t("pages.claimsDuration.continuousWeeksLabel")}
          hint={t("pages.claimsDuration.continuousWeeksHint")}
          name="temp.leave_details.continuous_leave_periods[0].weeks"
          value={valueWithFallback(continuousLeavePeriod.weeks)}
          onChange={handleInputChange}
          width="small"
        />
      </ConditionalContent>

      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "temp.leave_details.reduced_schedule_leave_periods[0]",
        ]}
        getField={getField}
        updateFields={updateFields}
        removeField={removeField}
        visible={duration_type_reduced}
        name="reduced_schedule_section"
      >
        <InputText
          inputMode="numeric"
          pattern="[0-9]*"
          label={t("pages.claimsDuration.reducedWeeksLabel")}
          hint={t("pages.claimsDuration.reducedWeeksHint")}
          name="temp.leave_details.reduced_schedule_leave_periods[0].weeks"
          value={valueWithFallback(reducedScheduleLeavePeriod.weeks)}
          onChange={handleInputChange}
          width="small"
        />
        <InputText
          inputMode="numeric"
          pattern="[0-9]*"
          label={t("pages.claimsDuration.reducedHoursPerWeekLabel")}
          hint={t("pages.claimsDuration.reducedHoursPerWeekHint")}
          name="temp.leave_details.reduced_schedule_leave_periods[0].hours_per_week"
          value={valueWithFallback(reducedScheduleLeavePeriod.hours_per_week)}
          onChange={handleInputChange}
          width="small"
        />
      </ConditionalContent>
      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "leave_details.intermittent_leave_periods[0]",
        ]}
        getField={getField}
        updateFields={updateFields}
        removeField={removeField}
        visible={duration_type_intermittent}
        name="intermittent_section"
      >
        <Heading level="2" size="1">
          {t("pages.claimsDuration.intermittentSectionLabel")}
        </Heading>
        <InputChoiceGroup
          choices={[
            {
              checked:
                intermittentLeavePeriod.frequency_interval_basis ===
                FrequencyIntervalBasis.weeks,
              label: t(
                "pages.claimsDuration.intermittentFrequencyBasisWeeksLabel"
              ),
              key: "per_week",
              value: FrequencyIntervalBasis.weeks,
            },
            {
              checked:
                intermittentLeavePeriod.frequency_interval_basis ===
                  FrequencyIntervalBasis.months &&
                intermittentLeavePeriod.frequency_interval === null,
              label: t(
                "pages.claimsDuration.intermittentFrequencyBasisMonthsLabel"
              ),
              key: "per_month",
              value: FrequencyIntervalBasis.months,
            },
            {
              checked:
                intermittentLeavePeriod.frequency_interval_basis ===
                  FrequencyIntervalBasis.months &&
                intermittentLeavePeriod.frequency_interval === 6,
              label: t(
                "pages.claimsDuration.intermittentFrequencyBasisDaysLabel"
              ),
              id: every6monthsId,
              key: every6monthsId,
              value: FrequencyIntervalBasis.months,
            },
          ]}
          label={t("pages.claimsDuration.intermittentFrequencyBasisLabel")}
          name="leave_details.intermittent_leave_periods[0].frequency_interval_basis"
          onChange={handleFrequencyBasisChange}
          type="radio"
          smallLabel
        />

        <ConditionalContent
          fieldNamesClearedWhenHidden={[
            "leave_details.intermittent_leave_periods[0].frequency",
          ]}
          getfield={getField}
          updateFields={updateFields}
          removeField={removeField}
          visible={!!intermittentLeavePeriod.frequency_interval_basis}
          name="frequency_question"
        >
          <InputText
            inputMode="numeric"
            pattern="[0-9]*"
            label={t("pages.claimsDuration.intermittentFrequencyLabel", {
              context:
                intermittentLeavePeriod.frequency_interval === 6
                  ? every6monthsId
                  : intermittentLeavePeriod.frequency_interval_basis,
            })}
            hint={t("pages.claimsDuration.intermittentFrequencyHint")}
            name="leave_details.intermittent_leave_periods[0].frequency"
            value={valueWithFallback(intermittentLeavePeriod.frequency)}
            onChange={handleInputChange}
            width="small"
            smallLabel
          />
        </ConditionalContent>

        <InputChoiceGroup
          choices={[
            {
              checked:
                intermittentLeavePeriod.duration_basis === DurationBasis.days,
              label: t(
                "pages.claimsDuration.intermittentDurationBasisDaysLabel"
              ),
              value: DurationBasis.days,
              key: "days",
            },
            {
              checked:
                intermittentLeavePeriod.duration_basis === DurationBasis.hours,
              label: t(
                "pages.claimsDuration.intermittentDurationBasisHoursLabel"
              ),
              value: DurationBasis.hours,
              key: "hours",
            },
          ]}
          label={t("pages.claimsDuration.intermittentDurationBasisLabel")}
          name="leave_details.intermittent_leave_periods[0].duration_basis"
          onChange={handleInputChange}
          type="radio"
          smallLabel
        />
        <ConditionalContent
          fieldNamesClearedWhenHidden={[
            "leave_details.intermittent_leave_periods[0].duration",
          ]}
          getField={getField}
          updateFields={updateFields}
          removeField={removeField}
          visible={!!intermittentLeavePeriod.duration_basis}
          name="duration_question"
        >
          <InputText
            inputMode="numeric"
            pattern="[0-9]*"
            label={t("pages.claimsDuration.intermittentDurationLabel", {
              context: intermittentLeavePeriod.duration_basis,
            })}
            hint={t("pages.claimsDuration.intermittentDurationHint")}
            name="leave_details.intermittent_leave_periods[0].duration"
            value={valueWithFallback(intermittentLeavePeriod.duration)}
            onChange={handleInputChange}
            width="small"
            smallLabel
          />
        </ConditionalContent>
      </ConditionalContent>
    </QuestionPage>
  );
};

Duration.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(Duration);
