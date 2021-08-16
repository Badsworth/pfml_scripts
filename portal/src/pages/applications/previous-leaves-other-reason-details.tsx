import PreviousLeave, { PreviousLeaveReason } from "../../models/PreviousLeave";
import { get, pick } from "lodash";
import BenefitsApplication from "../../models/BenefitsApplication";
import Details from "../../components/Details";
import Heading from "../../components/Heading";
import Hint from "../../components/Hint";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import InputHours from "../../components/InputHours";
import LeaveReason from "../../models/LeaveReason";
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
  "claim.previous_leaves_other_reason",
  "claim.previous_leaves_other_reason[*].is_for_current_employer",
  "claim.previous_leaves_other_reason[*].leave_end_date",
  "claim.previous_leaves_other_reason[*].leave_minutes",
  "claim.previous_leaves_other_reason[*].leave_reason",
  "claim.previous_leaves_other_reason[*].leave_start_date",
  "claim.previous_leaves_other_reason[*].previous_leave_id",
  "claim.previous_leaves_other_reason[*].worked_per_week_minutes",
];

export const PreviousLeavesOtherReasonDetails = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const limit = 6;

  const initialEntries = pick(props, fields).claim;
  if (initialEntries.previous_leaves_other_reason.length === 0) {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    initialEntries.previous_leaves_other_reason = [new PreviousLeave()];
  }

  // default to one existing previous leave.
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, updateFields } = useFormState(initialEntries);
  const previous_leaves_other_reason = get(
    formState,
    "previous_leaves_other_reason"
  );

  const leaveStartDate = formatDate(claim.leaveStartDate).full();

  const isCaringLeave = get(claim, "leave_details.reason") === LeaveReason.care;
  const previousLeaveStartDate = isCaringLeave
    ? formatDate("2021-07-01").full()
    : formatDate("2021-01-01").full();

  const handleSave = () => {
    return appLogic.benefitsApplications.update(
      claim.application_id,
      formState
    );
  };

  const handleAddClick = () => {
    updateFields({
      previous_leaves_other_reason: [
        ...previous_leaves_other_reason,
        // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
        new PreviousLeave(),
      ],
    });
  };

  const handleRemoveClick = (_entry, index) => {
    const updatedLeaves = [...previous_leaves_other_reason];
    updatedLeaves.splice(index, 1);
    updateFields({ previous_leaves_other_reason: updatedLeaves });
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const render = (entry, index) => {
    return (
      <PreviousLeavesOtherReasonDetailsCard
        claim={claim}
        entry={entry}
        index={index}
        getFunctionalInputProps={getFunctionalInputProps}
      />
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeavesOtherReasonDetails.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsPreviousLeavesOtherReasonDetails.sectionLabel")}
      </Heading>
      <Hint className="margin-bottom-3">
        {t("pages.claimsPreviousLeavesOtherReasonDetails.sectionHint", {
          previousLeaveStartDate,
          leaveStartDate,
        })}
      </Hint>

      <RepeatableFieldset
        addButtonLabel={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.addButton"
        )}
        entries={previous_leaves_other_reason}
        headingPrefix={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.previousLeaveEntryPrefix"
        )}
        onAddClick={handleAddClick}
        onRemoveClick={handleRemoveClick}
        removeButtonLabel={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.removeButton"
        )}
        render={render}
        limit={limit}
        limitMessage={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.limitMessage",
          { limit }
        )}
      />
    </QuestionPage>
  );
};

PreviousLeavesOtherReasonDetails.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export const PreviousLeavesOtherReasonDetailsCard = (props) => {
  const { t } = useTranslation();
  const {
    claim: { employer_fein },
    entry: { is_for_current_employer, leave_reason },
    getFunctionalInputProps,
    index,
  } = props;

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps(
          `previous_leaves_other_reason[${index}].leave_reason`
        )}
        smallLabel
        label={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.leaveReasonLabel"
        )}
        hint={t("pages.claimsPreviousLeavesOtherReasonDetails.leaveReasonHint")}
        type="radio"
        choices={[
          {
            label: t(
              "pages.claimsPreviousLeavesOtherReasonDetails.leaveReasonChoice_medical"
            ),
            value: PreviousLeaveReason.medical,
            checked: leave_reason === PreviousLeaveReason.medical,
          },
          {
            label: t(
              "pages.claimsPreviousLeavesOtherReasonDetails.leaveReasonChoice_pregnancy"
            ),
            value: PreviousLeaveReason.pregnancy,
            checked: leave_reason === PreviousLeaveReason.pregnancy,
          },
          {
            label: t(
              "pages.claimsPreviousLeavesOtherReasonDetails.leaveReasonChoice_bonding"
            ),
            value: PreviousLeaveReason.bonding,
            checked: leave_reason === PreviousLeaveReason.bonding,
          },
          {
            label: t(
              "pages.claimsPreviousLeavesOtherReasonDetails.leaveReasonChoice_care"
            ),
            value: PreviousLeaveReason.care,
            checked: leave_reason === PreviousLeaveReason.care,
          },
          {
            label: t(
              "pages.claimsPreviousLeavesOtherReasonDetails.leaveReasonChoice_activeDutyFamily"
            ),
            value: PreviousLeaveReason.activeDutyFamily,
            checked: leave_reason === PreviousLeaveReason.activeDutyFamily,
          },
          {
            label: t(
              "pages.claimsPreviousLeavesOtherReasonDetails.leaveReasonChoice_serviceMemberFamily"
            ),
            value: PreviousLeaveReason.serviceMemberFamily,
            checked: leave_reason === PreviousLeaveReason.serviceMemberFamily,
          },
        ]}
      />
      <InputChoiceGroup
        {...getFunctionalInputProps(
          `previous_leaves_other_reason[${index}].is_for_current_employer`
        )}
        smallLabel
        label={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.isForCurrentEmployerLabel",
          { employer_fein }
        )}
        hint={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.isForCurrentEmployerHint"
        )}
        type="radio"
        choices={[
          {
            label: t("pages.claimsPreviousLeavesOtherReasonDetails.choiceYes"),
            value: "true",
            checked: is_for_current_employer === true,
          },
          {
            label: t("pages.claimsPreviousLeavesOtherReasonDetails.choiceNo"),
            value: "false",
            checked: is_for_current_employer === false,
          },
        ]}
      />
      <InputDate
        {...getFunctionalInputProps(
          `previous_leaves_other_reason[${index}].leave_start_date`
        )}
        smallLabel
        label={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.leaveStartDateLabel"
        )}
        example={t("components.form.dateInputExample")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />
      <InputDate
        {...getFunctionalInputProps(
          `previous_leaves_other_reason[${index}].leave_end_date`
        )}
        smallLabel
        label={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.leaveEndDateLabel"
        )}
        example={t("components.form.dateInputExample")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />
      <InputHours
        {...getFunctionalInputProps(
          `previous_leaves_other_reason[${index}].worked_per_week_minutes`,
          { fallbackValue: null }
        )}
        label={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.workedPerWeekMinutesLabel"
        )}
        smallLabel
        hoursLabel={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.hoursLabel"
        )}
        minutesLabel={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.minutesLabel"
        )}
        hint={
          <React.Fragment>
            <p>
              {t(
                "pages.claimsPreviousLeavesOtherReasonDetails.workedPerWeekMinutesHint"
              )}
            </p>
            <Details
              label={t(
                "pages.claimsPreviousLeavesOtherReasonDetails.workedPerWeekMinutesDetailsLabel"
              )}
            >
              <Trans i18nKey="pages.claimsPreviousLeavesOtherReasonDetails.workedPerWeekMinutesDetails" />
            </Details>
          </React.Fragment>
        }
        minutesIncrement={15}
      />
      <InputHours
        {...getFunctionalInputProps(
          `previous_leaves_other_reason[${index}].leave_minutes`,
          { fallbackValue: null }
        )}
        label={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.leaveMinutesLabel"
        )}
        smallLabel
        hoursLabel={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.hoursLabel"
        )}
        minutesLabel={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.minutesLabel"
        )}
        hint={t(
          "pages.claimsPreviousLeavesOtherReasonDetails.leaveMinutesHint"
        )}
        minutesIncrement={15}
      />
    </React.Fragment>
  );
};

PreviousLeavesOtherReasonDetailsCard.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  entry: PropTypes.instanceOf(PreviousLeave).isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
  index: PropTypes.number.isRequired,
};

export default withBenefitsApplication(PreviousLeavesOtherReasonDetails);
