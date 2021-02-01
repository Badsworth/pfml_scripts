import Claim from "../../models/Claim";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.has_other_incomes",
  "claim.other_incomes_awaiting_approval",
];

export const OtherIncomes = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  /**
   * The radio choices correspond to both has_other_incomes and
   * other_incomes_awaiting_approval, so this callback determines how those
   * booleans should be set by the value of the choice input.
   * @param {SyntheticEvent} event - Change event
   */
  const handleHasOtherIncomesChange = (event) => {
    if (event.target.value === "yes") {
      updateFields({
        has_other_incomes: true,
        other_incomes_awaiting_approval: false,
      });
    } else if (event.target.value === "no") {
      const fieldValues = {
        has_other_incomes: false,
        other_incomes_awaiting_approval: false,
      };
      if (claim.other_incomes.length) {
        fieldValues.other_incomes = null;
      }
      updateFields(fieldValues);
    } else if (event.target.value === "pending") {
      updateFields({
        has_other_incomes: false,
        other_incomes_awaiting_approval: true,
      });
    }
  };

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });
  const hintList = t("pages.claimsOtherIncomes.hintList", {
    returnObjects: true,
  });

  return (
    <QuestionPage
      title={t("pages.claimsOtherIncomes.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_other_incomes")}
        onChange={handleHasOtherIncomesChange}
        choices={[
          {
            checked:
              formState.has_other_incomes === true &&
              formState.other_incomes_awaiting_approval === false,
            label: t("pages.claimsOtherIncomes.choiceYes"),
            value: "yes",
          },
          {
            checked:
              formState.has_other_incomes === false &&
              formState.other_incomes_awaiting_approval === false,
            label: t("pages.claimsOtherIncomes.choiceNo"),
            value: "no",
          },
          {
            checked:
              formState.has_other_incomes === false &&
              formState.other_incomes_awaiting_approval === true,
            label: t("pages.claimsOtherIncomes.choicePendingOtherIncomes"),
            value: "pending",
          },
        ]}
        label={t("pages.claimsOtherIncomes.sectionLabel")}
        type="radio"
        hint={
          <React.Fragment>
            <LeaveDatesAlert
              startDate={claim.leaveStartDate}
              endDate={claim.leaveEndDate}
            />
            <p>{t("pages.claimsOtherIncomes.hintHeader")}</p>
            <ul className="usa-list">
              {hintList.map((listItem, index) => (
                <li key={index}>{listItem}</li>
              ))}
            </ul>
          </React.Fragment>
        }
      />
    </QuestionPage>
  );
};

OtherIncomes.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(OtherIncomes);
