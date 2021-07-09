import { get, pick } from "lodash";
import BenefitsApplication from "../../models/BenefitsApplication";
import Details from "../../components/Details";
import Heading from "../../components/Heading";
import Hint from "../../components/Hint";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import InputHours from "../../components/InputHours";
import LeaveReason from "../../models/LeaveReason";
import PreviousLeave from "../../models/PreviousLeave";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../components/RepeatableFieldset";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [
  "claim.previous_leaves_same_reason",
  "claim.previous_leaves_same_reason[*].is_for_current_employer",
  "claim.previous_leaves_same_reason[*].leave_end_date",
  "claim.previous_leaves_same_reason[*].leave_minutes",
  "claim.previous_leaves_same_reason[*].leave_start_date",
  "claim.previous_leaves_same_reason[*].worked_per_week_minutes",
];

export const PreviousLeavesSameReasonDetails = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const limit = 6;

  const initialEntries = pick(props, fields).claim;
  if (initialEntries.previous_leaves_same_reason.length === 0) {
    initialEntries.previous_leaves_same_reason = [new PreviousLeave()];
  }

  // default to one existing previous leave.
  const { formState, updateFields } = useFormState(initialEntries);
  const previous_leaves_same_reason = get(
    formState,
    "previous_leaves_same_reason"
  );

  const leaveStartDate = formatDate(claim.leaveStartDate).full();

  const isCaringLeave = get(claim, "leave_details.reason") === LeaveReason.care;
  const previousLeaveStartDate = isCaringLeave
    ? formatDate("2021-07-01").full()
    : formatDate("2021-01-01").full();

  const handleSave = () => {
    appLogic.benefitsApplications.update(claim.application_id, formState);
  };

  const handleAddClick = () => {
    updateFields({
      previous_leaves_same_reason: [
        ...previous_leaves_same_reason,
        new PreviousLeave(),
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

      <Hint className="margin-bottom-3">
        {t("pages.claimsPreviousLeavesSameReasonDetails.sectionHint", {
          previousLeaveStartDate,
          leaveStartDate,
        })}
      </Hint>
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
          <React.Fragment>
            <p>
              {t(
                "pages.claimsPreviousLeavesSameReasonDetails.workedPerWeekMinutesHint"
              )}
            </p>
            <Details
              label={t(
                "pages.claimsPreviousLeavesSameReasonDetails.workedPerWeekMinutesDetailsLabel"
              )}
            >
              <Trans i18nKey="pages.claimsPreviousLeavesSameReasonDetails.workedPerWeekMinutesDetails" />
            </Details>
          </React.Fragment>
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
