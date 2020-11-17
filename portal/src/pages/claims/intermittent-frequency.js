import Claim, {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../../models/Claim";
import { get, pick } from "lodash";
import Alert from "../../components/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import findKeyByValue from "../../utils/findKeyByValue";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

/**
 * Convenience constant for referencing the leave period object
 * and referencing fields within it
 */
const leavePeriodPath = "leave_details.intermittent_leave_periods[0]";

export const fields = [
  `claim.${leavePeriodPath}.frequency_interval_basis`,
  `claim.${leavePeriodPath}.frequency_interval`,
  `claim.${leavePeriodPath}.frequency`,
  `claim.${leavePeriodPath}.duration_basis`,
  `claim.${leavePeriodPath}.duration`,
  `claim.${leavePeriodPath}.leave_period_id`,
];

/**
 * ID used for the "Irregular over 6 months" field, which
 * drives some dynamic behavior like updating multiple API fields
 * via a single input in the interface. Exported to support our tests.
 */
export const irregularOver6MonthsId = "irregularOver6Months";

export const IntermittentFrequency = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const leavePeriod = new IntermittentLeavePeriod(
    get(formState, leavePeriodPath)
  );

  const handleInputChange = useHandleInputChange(updateFields);

  /**
   * The "Irregular over the next 6 months" radio choice for intermittentLeavePeriod.frequency_interval_basis
   * corresponds to both frequency_interval_basis and frequency_interval fields
   * e.g 6 (frequency interval) months (frequency interval basis)
   * This callback determines whether the frequency interval should be set
   * by the id of the choice input.
   * @param {SyntheticEvent} event - Change event
   */
  const handleFrequencyIntervalBasisChange = (event) => {
    const frequency_interval =
      event.target.id === irregularOver6MonthsId ? 6 : null;

    updateFields({
      [`${leavePeriodPath}.frequency_interval`]: frequency_interval,
    });

    // Call the normal change handler so frequency_interval_basis is also updated:
    handleInputChange(event);
  };

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsIntermittentFrequency.title")}
      onSave={handleSave}
    >
      {claim.isMedicalLeave && (
        <Alert state="info" neutral>
          {t("pages.claimsIntermittentFrequency.medicalAlert")}
        </Alert>
      )}

      <Heading level="2" size="1">
        {t("pages.claimsIntermittentFrequency.sectionLabel")}
      </Heading>

      <InputChoiceGroup
        {...getFunctionalInputProps(
          `${leavePeriodPath}.frequency_interval_basis`
        )}
        onChange={handleFrequencyIntervalBasisChange}
        choices={[
          {
            checked:
              leavePeriod.frequency_interval_basis ===
              FrequencyIntervalBasis.weeks,
            label: t("pages.claimsIntermittentFrequency.frequencyBasisChoice", {
              context: "weeks",
            }),
            value: FrequencyIntervalBasis.weeks,
          },
          {
            checked:
              leavePeriod.frequency_interval_basis ===
                FrequencyIntervalBasis.months &&
              leavePeriod.frequency_interval === null,
            label: t("pages.claimsIntermittentFrequency.frequencyBasisChoice", {
              context: "months",
            }),
            value: FrequencyIntervalBasis.months,
          },
          {
            checked:
              leavePeriod.frequency_interval_basis ===
                FrequencyIntervalBasis.months &&
              leavePeriod.frequency_interval === 6,
            label: t("pages.claimsIntermittentFrequency.frequencyBasisChoice", {
              context: "irregular",
            }),
            id: irregularOver6MonthsId,
            // This choice shares the same value as another choice, which the
            // component uses as its key by default, so we override that here
            // so that each choice has its own unique key:
            key: irregularOver6MonthsId,
            value: FrequencyIntervalBasis.months,
          },
        ]}
        label={t("pages.claimsIntermittentFrequency.frequencyBasisLabel")}
        hint={
          claim.isMedicalLeave
            ? t("pages.claimsIntermittentFrequency.frequencyBasisHint_medical")
            : null // could use `context` if another leave type needs hint text
        }
        type="radio"
        smallLabel
      />

      <ConditionalContent visible={!!leavePeriod.frequency_interval_basis}>
        <InputText
          {...getFunctionalInputProps(`${leavePeriodPath}.frequency`)}
          inputMode="numeric"
          pattern="[0-9]*"
          label={t("pages.claimsIntermittentFrequency.frequencyLabel", {
            context:
              leavePeriod.frequency_interval === 6
                ? "irregular"
                : findKeyByValue(
                    FrequencyIntervalBasis,
                    leavePeriod.frequency_interval_basis
                  ),
          })}
          hint={
            claim.isMedicalLeave
              ? t("pages.claimsIntermittentFrequency.frequencyHint_medical")
              : null // could use `context` if another leave type needs hint text
          }
          width="small"
          smallLabel
        />

        <InputChoiceGroup
          {...getFunctionalInputProps(`${leavePeriodPath}.duration_basis`)}
          choices={[
            {
              checked: leavePeriod.duration_basis === DurationBasis.days,
              label: t(
                "pages.claimsIntermittentFrequency.durationBasisChoice",
                { context: "days" }
              ),
              value: DurationBasis.days,
            },
            {
              checked: leavePeriod.duration_basis === DurationBasis.hours,
              label: t(
                "pages.claimsIntermittentFrequency.durationBasisChoice",
                { context: "hours" }
              ),
              value: DurationBasis.hours,
            },
          ]}
          label={t("pages.claimsIntermittentFrequency.durationBasisLabel")}
          hint={
            claim.isMedicalLeave
              ? t("pages.claimsIntermittentFrequency.durationBasisHint_medical")
              : null // could use `context` if another leave type needs hint text
          }
          type="radio"
          smallLabel
        />
      </ConditionalContent>

      <ConditionalContent visible={!!leavePeriod.duration_basis}>
        <InputText
          {...getFunctionalInputProps(`${leavePeriodPath}.duration`)}
          inputMode="numeric"
          pattern="[0-9]*"
          label={t("pages.claimsIntermittentFrequency.durationLabel", {
            context: findKeyByValue(DurationBasis, leavePeriod.duration_basis),
          })}
          hint={
            claim.isMedicalLeave
              ? t("pages.claimsIntermittentFrequency.durationHint_medical")
              : null // could use `context` if another leave type needs hint text
          }
          width="small"
          smallLabel
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

IntermittentFrequency.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(IntermittentFrequency);
