import Claim from "../../models/Claim";
import Heading from "../../components/Heading";
import InputDate from "../../components/InputDate";
import PreviousLeave from "../../models/PreviousLeave";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../components/RepeatableFieldset";
import get from "lodash/get";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.previous_leaves"];

export const PreviousLeavesDetails = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const initialEntries = pick(props, fields).claim;
  // If the claim doesn't have any relevant entries, pre-populate the first one
  // so that it renders in the RepeatableFieldset below
  if (initialEntries.previous_leaves.length === 0) {
    initialEntries.previous_leaves = [new PreviousLeave()];
  }
  const { formState, updateFields } = useFormState(initialEntries);
  const previous_leaves = get(formState, "previous_leaves");

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const handleAddClick = () => {
    const updatedEntries = previous_leaves.concat([new PreviousLeave()]);
    updateFields({ previous_leaves: updatedEntries });
  };
  const handleRemoveClick = (entry, index) => {
    const updatedEntries = [...previous_leaves];
    updatedEntries.splice(index, 1);
    updateFields({ previous_leaves: updatedEntries });
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const render = (entry, index) => {
    return (
      <PreviousLeaveCard
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
      />
    </QuestionPage>
  );
};

PreviousLeavesDetails.propTypes = {
  claim: PropTypes.instanceOf(Claim),
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
  const { index, getFunctionalInputProps } = props;

  return (
    <React.Fragment>
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
  index: PropTypes.number.isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
};

export default withClaim(PreviousLeavesDetails);
