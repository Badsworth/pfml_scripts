import { get, pick } from "lodash";

import BenefitsApplication from "../../models/BenefitsApplication";
import IconHeading from "../../components/IconHeading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import formatDate from "../../utils/formatDate";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.has_previous_leaves_other_reason"];

export const PreviousLeavesOtherReason = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const leaveStartDate = formatDate(claim.leaveStartDate).full();

  const hintList = t("pages.claimsPreviousLeavesOtherReason.hintList", {
    returnObjects: true,
  });

  const handleSave = async () => {
    const patchData = { ...formState };
    if (
      patchData.has_previous_leaves_other_reason === false &&
      get(claim, "previous_leaves_other_reason.length")
    ) {
      patchData.previous_leaves_other_reason = null;
    }
    return await appLogic.benefitsApplications.update(
      claim.application_id,
      patchData
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeavesOtherReason.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_previous_leaves_other_reason")}
        type="radio"
        choices={[
          {
            checked: formState.has_previous_leaves_other_reason === true,
            hint: t("pages.claimsPreviousLeavesOtherReason.hintTextYes"),
            label: t("pages.claimsPreviousLeavesOtherReason.choiceYes"),
            value: "true",
          },
          {
            checked: formState.has_previous_leaves_other_reason === false,
            hint: t("pages.claimsPreviousLeavesOtherReason.hintTextNo"),
            label: t("pages.claimsPreviousLeavesOtherReason.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsPreviousLeavesOtherReason.sectionLabel", {
          leaveStartDate,
        })}
        hint={
          <React.Fragment>
            <IconHeading name="check_circle">
              {t("pages.claimsPreviousLeavesOtherReason.hintDoHeader")}
            </IconHeading>
            <ul className="usa-list margin-left-2">
              {hintList.map((listItem, index) => (
                <li key={index}>{listItem}</li>
              ))}
            </ul>
            <IconHeading name="cancel">
              {t("pages.claimsPreviousLeavesOtherReason.hintDontHeader")}
            </IconHeading>
            <ul className="usa-list margin-left-2">
              <li>
                {t(
                  "pages.claimsPreviousLeavesOtherReason.leaveTakenThroughPFML"
                )}
              </li>
            </ul>
          </React.Fragment>
        }
      />
    </QuestionPage>
  );
};

PreviousLeavesOtherReason.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(PreviousLeavesOtherReason);
