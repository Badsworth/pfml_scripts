import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import BenefitsApplication from "../../models/BenefitsApplication";
import Details from "../../components/core/Details";
import Heading from "../../components/core/Heading";
import Hint from "../../components/core/Hint";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import InputDate from "../../components/core/InputDate";
import InputHours from "../../components/core/InputHours";
import PreviousLeave from "../../models/PreviousLeave";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../components/core/RepeatableFieldset";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = [
  "claim.previous_leaves_same_reason",
  "claim.previous_leaves_same_reason[*].is_for_current_employer",
  "claim.previous_leaves_same_reason[*].leave_end_date",
  "claim.previous_leaves_same_reason[*].leave_minutes",
  "claim.previous_leaves_same_reason[*].leave_start_date",
  "claim.previous_leaves_same_reason[*].worked_per_week_minutes",
];

export const PreviousLeavesSameReasonDetails = (
  props: WithBenefitsApplicationProps
) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const limit = 6;

  const initialEntries = pick(props, fields).claim || {
    previous_leaves_same_reason: [],
  };

  if (initialEntries.previous_leaves_same_reason.length === 0) {
    initialEntries.previous_leaves_same_reason = [new PreviousLeave({})];
  }

  // default to one existing previous leave.

  const { formState, updateFields } = useFormState(initialEntries);
  const previous_leaves_same_reason = get(
    formState,
    "previous_leaves_same_reason"
  );

  const leaveStartDate = formatDate(claim.leaveStartDate).full();
  const previousLeaveStartDate = formatDate(
    claim.computed_start_dates.same_reason
  ).full();

  const handleSave = () => {
    return appLogic.benefitsApplications.update(
      claim.application_id,
      formState
    );
  };

  const handleAddClick = () => {
    updateFields({
      previous_leaves_same_reason: [
        ...previous_leaves_same_reason,
        new PreviousLeave({}),
      ],
    });
  };

  const handleRemoveClick = (_entry: PreviousLeave, index: number) => {
    const updatedLeaves = [...previous_leaves_same_reason];
    updatedLeaves.splice(index, 1);
    updateFields({ previous_leaves_same_reason: updatedLeaves });
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const render = (entry: PreviousLeave, index: number) => {
    return (
      <PreviousLeaveSameReasonDetailsCard
        claim={claim}
        entry={entry}
        index={index}
        getFunctionalInputProps={getFunctionalInputProps}
        minimumDate={previousLeaveStartDate}
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
        <Trans
          i18nKey="pages.claimsPreviousLeavesOtherReasonDetails.sectionHint"
          components={{
            previousLeaveStartDate,
            leaveStartDate,
          }}
        />
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

interface PreviousLeaveSameReasonDetailsCardProps {
  claim: BenefitsApplication;
  entry: PreviousLeave;
  getFunctionalInputProps: ReturnType<typeof useFunctionalInputProps>;
  index: number;
  minimumDate: string;
}

export const PreviousLeaveSameReasonDetailsCard = (
  props: PreviousLeaveSameReasonDetailsCardProps
) => {
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
        hint={t(
          "pages.claimsPreviousLeavesSameReasonDetails.leaveStartDateHint",
          {
            minimumDate: props.minimumDate,
          }
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
        hint={t(
          "pages.claimsPreviousLeavesSameReasonDetails.leaveEndDateHint",
          {
            minimumDate: props.minimumDate,
          }
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

export default withBenefitsApplication(PreviousLeavesSameReasonDetails);
