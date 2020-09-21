import Claim, {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
  LeaveReason,
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
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.temp.leave_details.continuous_leave_periods[0]",
  "claim.temp.leave_details.reduced_schedule_leave_periods[0]",
  "claim.leave_details.intermittent_leave_periods[0]",
];

export const every6monthsId = "every6months";

export const Duration = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, removeField } = useFormState({
    ...pick(props, fields).claim,
    duration_type_continuous: claim.isContinuous,
    duration_type_reduced: claim.isReducedSchedule,
    duration_type_intermittent: claim.isIntermittent,
  });
  const {
    duration_type_continuous,
    duration_type_intermittent,
    duration_type_reduced,
  } = formState;
  const intermittentLeavePeriod = new IntermittentLeavePeriod(
    get(formState, "leave_details.intermittent_leave_periods[0]")
  );
  const leave_reason = get(claim, "leave_details.reason");
  const contentContext =
    leave_reason === LeaveReason.bonding ? "bonding" : "medical";

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

  const handleSave = async () => {
    const {
      duration_type_continuous,
      duration_type_intermittent,
      duration_type_reduced,
      ...patchData
    } = formState;

    await appLogic.claims.update(claim.application_id, patchData);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage title={t("pages.claimsDuration.title")} onSave={handleSave}>
      <InputChoiceGroup
        {...getFunctionalInputProps("duration_type")}
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
            <p>
              {t("pages.claimsDuration.durationTypeSectionHint", {
                context: contentContext,
              })}
            </p>
            <p>{t("pages.claimsDuration.durationTypeSelectAllHint")}</p>
          </React.Fragment>
        }
        type="checkbox"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "temp.leave_details.reduced_schedule_leave_periods",
        ]}
        getField={getField}
        updateFields={updateFields}
        removeField={removeField}
        visible={duration_type_reduced}
        name="reduced_schedule_section"
      >
        <InputText
          {...getFunctionalInputProps(
            "temp.leave_details.reduced_schedule_leave_periods[0].weeks"
          )}
          inputMode="numeric"
          pattern="[0-9]*"
          label={t("pages.claimsDuration.reducedWeeksLabel")}
          hint={t("pages.claimsDuration.reducedWeeksHint")}
          width="small"
        />
        <InputText
          {...getFunctionalInputProps(
            "temp.leave_details.reduced_schedule_leave_periods[0].hours_per_week"
          )}
          inputMode="numeric"
          pattern="[0-9]*"
          label={t("pages.claimsDuration.reducedHoursPerWeekLabel")}
          hint={t("pages.claimsDuration.reducedHoursPerWeekHint")}
          width="small"
        />
      </ConditionalContent>
      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "leave_details.intermittent_leave_periods",
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
          {...getFunctionalInputProps(
            "leave_details.intermittent_leave_periods[0].frequency_interval_basis"
          )}
          onChange={handleFrequencyBasisChange}
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
          type="radio"
          smallLabel
        />

        <ConditionalContent
          fieldNamesClearedWhenHidden={[
            "leave_details.intermittent_leave_periods[0].frequency",
          ]}
          getField={getField}
          updateFields={updateFields}
          removeField={removeField}
          visible={!!intermittentLeavePeriod.frequency_interval_basis}
          name="frequency_question"
        >
          <InputText
            {...getFunctionalInputProps(
              "leave_details.intermittent_leave_periods[0].frequency"
            )}
            inputMode="numeric"
            pattern="[0-9]*"
            label={t("pages.claimsDuration.intermittentFrequencyLabel", {
              context:
                intermittentLeavePeriod.frequency_interval === 6
                  ? every6monthsId
                  : intermittentLeavePeriod.frequency_interval_basis,
            })}
            hint={t("pages.claimsDuration.intermittentFrequencyHint")}
            width="small"
            smallLabel
          />
        </ConditionalContent>

        <InputChoiceGroup
          {...getFunctionalInputProps(
            "leave_details.intermittent_leave_periods[0].duration_basis"
          )}
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
            {...getFunctionalInputProps(
              "leave_details.intermittent_leave_periods[0].duration"
            )}
            inputMode="numeric"
            pattern="[0-9]*"
            label={t("pages.claimsDuration.intermittentDurationLabel", {
              context: intermittentLeavePeriod.duration_basis,
            })}
            hint={t("pages.claimsDuration.intermittentDurationHint")}
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
