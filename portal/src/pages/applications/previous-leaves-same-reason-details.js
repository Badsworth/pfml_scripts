import PreviousLeave, { PreviousLeaveReason } from "../../models/PreviousLeave";
import { get, pick } from "lodash";
import BenefitsApplication from "../../models/BenefitsApplication";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import InputHours from "../../components/InputHours";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../components/RepeatableFieldset";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [
  "claim.previous_leaves_same_reason",
  "claim.previous_leaves_same_reason[*].is_for_current_employer",
  "claim.previous_leaves_same_reason[*].leave_end_date",
  "claim.previous_leaves_same_reason[*].leave_minutes",
  "claim.previous_leaves_same_reason[*].leave_reason",
  "claim.previous_leaves_same_reason[*].leave_start_date",
  "claim.previous_leaves_same_reason[*].worked_per_week_minutes",
];

export const PreviousLeavesSameReasonDetails = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const limit = 6;

  /**
   * Converts a LeaveReason to its corresponding PreviousLeaveReason.
   * @param {string} leaveReason - the application leave reason
   * @returns the corresponding PreviousLeaveReason
   */
  const leaveReasonToPreviousLeaveReason = (leaveReason) => {
    const previousLeaveReasonKey = findKeyByValue(LeaveReason, leaveReason);
    return PreviousLeaveReason[previousLeaveReasonKey];
  };

  const initialEntries = pick(props, fields).claim;
  if (initialEntries.previous_leaves_same_reason.length === 0) {
    const leave_reason = leaveReasonToPreviousLeaveReason(
      claim.leave_details.reason
    );
    initialEntries.previous_leaves_same_reason = [
      new PreviousLeave({
        leave_reason,
      }),
    ];
  }

  // default to one existing previous leave.
  const { formState, updateFields } = useFormState(initialEntries);
  const previous_leaves_same_reason = get(
    formState,
    "previous_leaves_same_reason"
  );

  const handleSave = () => {
    appLogic.benefitsApplications.update(claim.application_id, formState);
  };

  const handleAddClick = () => {
    const leave_reason = leaveReasonToPreviousLeaveReason(
      claim.leave_details.reason
    );
    updateFields({
      previous_leaves_same_reason: [
        ...previous_leaves_same_reason,
        new PreviousLeave({ leave_reason }),
      ],
    });
  };

  const handleRemoveClick = (_entry, index) => {
    const updatedLeaves = [...previous_leaves_same_reason];
    updatedLeaves.splice(index, 1);
    updateFields({ previous_leaves_same_reason: updatedLeaves });
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const render = (entry, index) => {
    return (
      <PreviousLeaveSameReasonDetailsCard
        claim={claim}
        entry={entry}
        index={index}
        getFunctionalInputProps={getFunctionalInputProps}
      />
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeavesSameReasonDetails.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsPreviousLeavesSameReasonDetails.sectionLabel")}
      </Heading>

      <RepeatableFieldset
        addButtonLabel={t(
          "pages.claimsPreviousLeavesSameReasonDetails.addButton"
        )}
        entries={previous_leaves_same_reason}
        headingPrefix={t(
          "pages.claimsPreviousLeavesSameReasonDetails.previousLeaveEntryPrefix"
        )}
        onAddClick={handleAddClick}
        onRemoveClick={handleRemoveClick}
        removeButtonLabel={t(
          "pages.claimsPreviousLeavesSameReasonDetails.removeButton"
        )}
        render={render}
        limit={limit}
        limitMessage={t(
          "pages.claimsPreviousLeavesSameReasonDetails.limitMessage",
          { limit }
        )}
      />
    </QuestionPage>
  );
};

PreviousLeavesSameReasonDetails.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export const PreviousLeaveSameReasonDetailsCard = (props) => {
  const { t } = useTranslation();
  const {
    claim: { employer_fein },
    entry: { is_for_current_employer },
    getFunctionalInputProps,
    index,
  } = props;

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps(
          `previous_leaves_same_reason[${index}].is_for_current_employer`
        )}
        smallLabel
        label={t(
          "pages.claimsPreviousLeavesSameReasonDetails.isForCurrentEmployerLabel",
          { employer_fein }
        )}
        hint={t(
          "pages.claimsPreviousLeavesSameReasonDetails.isForCurrentEmployerHint"
        )}
        type="radio"
        choices={[
          {
            label: t("pages.claimsPreviousLeavesSameReasonDetails.choiceYes"),
            value: "true",
            checked: is_for_current_employer === true,
          },
          {
            label: t("pages.claimsPreviousLeavesSameReasonDetails.choiceNo"),
            value: "false",
            checked: is_for_current_employer === false,
          },
        ]}
      />
      <InputDate
        {...getFunctionalInputProps(
          `previous_leaves_same_reason[${index}].leave_start_date`
        )}
        smallLabel
        label={t(
          "pages.claimsPreviousLeavesSameReasonDetails.leaveStartDateLabel"
        )}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />
      <InputDate
        {...getFunctionalInputProps(
          `previous_leaves_same_reason[${index}].leave_end_date`
        )}
        smallLabel
        label={t(
          "pages.claimsPreviousLeavesSameReasonDetails.leaveEndDateLabel"
        )}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />
      <InputHours
        {...getFunctionalInputProps(
          `previous_leaves_same_reason[${index}].worked_per_week_minutes`,
          { fallbackValue: null }
        )}
        label={t(
          "pages.claimsPreviousLeavesSameReasonDetails.workedPerWeekMinutesLabel"
        )}
        smallLabel
        hoursLabel={t("pages.claimsPreviousLeavesSameReasonDetails.hoursLabel")}
        minutesLabel={t(
          "pages.claimsPreviousLeavesSameReasonDetails.minutesLabel"
        )}
        hint={
          <Trans i18nKey="pages.claimsPreviousLeavesSameReasonDetails.workedPerWeekMinutesHint" />
        }
        minutesIncrement={15}
      />
      <InputHours
        {...getFunctionalInputProps(
          `previous_leaves_same_reason[${index}].leave_minutes`,
          { fallbackValue: null }
        )}
        label={t(
          "pages.claimsPreviousLeavesSameReasonDetails.leaveMinutesLabel"
        )}
        smallLabel
        hoursLabel={t("pages.claimsPreviousLeavesSameReasonDetails.hoursLabel")}
        minutesLabel={t(
          "pages.claimsPreviousLeavesSameReasonDetails.minutesLabel"
        )}
        hint={t("pages.claimsPreviousLeavesSameReasonDetails.leaveMinutesHint")}
        minutesIncrement={15}
      />
    </React.Fragment>
  );
};

PreviousLeaveSameReasonDetailsCard.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  entry: PropTypes.instanceOf(PreviousLeave).isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
  index: PropTypes.number.isRequired,
};

export default withBenefitsApplication(PreviousLeavesSameReasonDetails);
