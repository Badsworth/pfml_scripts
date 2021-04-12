import PreviousLeave, { PreviousLeaveReason } from "../../models/PreviousLeave";
import React, { useEffect, useRef } from "react";
import { get, pick } from "lodash";
import BenefitsApplication from "../../models/BenefitsApplication";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import RepeatableFieldset from "../../components/RepeatableFieldset";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.previous_leaves",
  "claim.previous_leaves[*].is_for_current_employer",
  "claim.previous_leaves[*].leave_end_date",
  "claim.previous_leaves[*].leave_reason",
  "claim.previous_leaves[*].leave_start_date",
];

export const PreviousLeavesDetails = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const useInitialEntries = useRef(true);

  const initialEntries = pick(props, fields).claim;
  // If the claim doesn't have any relevant entries, pre-populate the first one
  // so that it renders in the RepeatableFieldset below
  if (initialEntries.previous_leaves.length === 0) {
    initialEntries.previous_leaves = [new PreviousLeave()];
  }
  const { formState, updateFields } = useFormState(initialEntries);
  const previous_leaves = get(formState, "previous_leaves");
  const employer_fein = get(claim, "employer_fein");

  useEffect(() => {
    // Don't bother calling updateFields() when the page first renders
    if (useInitialEntries.current) {
      useInitialEntries.current = false;
      return;
    }

    // When there's a validation error, we get back the list of previous_leaves with previous_leave_ids from the API
    // When claim.previous_leaves updates, we also need to update the formState values to include the previous_leave_ids,
    // so on subsequent submits, we don't create new previous_leave records
    updateFields({ previous_leaves: claim.previous_leaves });
  }, [claim.previous_leaves, updateFields]);

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const handleAddClick = () => {
    const updatedEntries = previous_leaves.concat([new PreviousLeave()]);
    updateFields({ previous_leaves: updatedEntries });
  };

  const otherLeaves = appLogic.otherLeaves;
  const handleRemoveClick = async (entry, index) => {
    let entrySavedToApi = !!entry.previous_leave_id;
    if (entrySavedToApi) {
      // Try to delete the entry from the API
      const success = await otherLeaves.removePreviousLeave(
        claim.application_id,
        entry.previous_leave_id
      );
      entrySavedToApi = !success;
    }

    if (!entrySavedToApi) {
      const updatedEntries = [...previous_leaves];
      updatedEntries.splice(index, 1);
      updateFields({ previous_leaves: updatedEntries });
    }
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const render = (entry, index) => {
    return (
      <PreviousLeaveCard
        employer_fein={employer_fein}
        entry={entry}
        getFunctionalInputProps={getFunctionalInputProps}
        index={index}
      />
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeavesDetails.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsPreviousLeavesDetails.sectionLabel")}
      </Heading>

      <RepeatableFieldset
        addButtonLabel={t("pages.claimsPreviousLeavesDetails.addButton")}
        entries={previous_leaves}
        headingPrefix={t("pages.claimsPreviousLeavesDetails.cardHeadingPrefix")}
        onAddClick={handleAddClick}
        onRemoveClick={handleRemoveClick}
        removeButtonLabel={t("pages.claimsPreviousLeavesDetails.removeButton")}
        render={render}
        limit={6}
        limitMessage={t("pages.claimsPreviousLeavesDetails.limitMessage")}
      />
    </QuestionPage>
  );
};

PreviousLeavesDetails.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

/**
 * Group of fields for a PreviousLeave instance
 */
export const PreviousLeaveCard = (props) => {
  const { t } = useTranslation();
  const { employer_fein, entry, index, getFunctionalInputProps } = props;

  // Get field values from entry, which represents what's in the form state
  const is_for_current_employer = entry.is_for_current_employer;
  const leave_reason = entry.leave_reason;

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps(
          `previous_leaves[${index}].is_for_current_employer`
        )}
        choices={[
          {
            checked: is_for_current_employer === true,
            label: t(
              "pages.claimsPreviousLeavesDetails.currentEmployerChoice_yes"
            ),
            value: "true",
          },
          {
            checked: is_for_current_employer === false,
            label: t(
              "pages.claimsPreviousLeavesDetails.currentEmployerChoice_no"
            ),
            value: "false",
          },
        ]}
        label={t("pages.claimsPreviousLeavesDetails.currentEmployerLabel", {
          employer_fein,
        })}
        type="radio"
        smallLabel
      />

      <InputChoiceGroup
        {...getFunctionalInputProps(`previous_leaves[${index}].leave_reason`)}
        choices={[
          "medical",
          "pregnancy",
          "bonding",
          "care",
          "activeDutyFamily",
          "serviceMemberFamily",
        ].map((reasonKey) => ({
          checked: leave_reason === PreviousLeaveReason[reasonKey],
          label: t("pages.claimsPreviousLeavesDetails.leaveReasonChoice", {
            context: reasonKey,
          }),
          value: PreviousLeaveReason[reasonKey],
        }))}
        label={t("pages.claimsPreviousLeavesDetails.leaveReasonLabel")}
        type="radio"
        smallLabel
      />

      <InputDate
        {...getFunctionalInputProps(
          `previous_leaves[${index}].leave_start_date`
        )}
        label={t("pages.claimsPreviousLeavesDetails.startDateLabel")}
        example={t("components.form.dateInputExample")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <InputDate
        {...getFunctionalInputProps(`previous_leaves[${index}].leave_end_date`)}
        label={t("pages.claimsPreviousLeavesDetails.endDateLabel")}
        example={t("components.form.dateInputExample")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
    </React.Fragment>
  );
};

PreviousLeaveCard.propTypes = {
  employer_fein: PropTypes.string.isRequired,
  entry: PropTypes.instanceOf(PreviousLeave).isRequired,
  index: PropTypes.number.isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
};

export default withClaim(PreviousLeavesDetails);
