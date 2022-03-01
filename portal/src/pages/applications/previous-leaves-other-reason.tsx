import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Heading from "../../components/core/Heading";
import Icon from "../../components/core/Icon";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.has_previous_leaves_other_reason"];

export const PreviousLeavesOtherReason = (
  props: WithBenefitsApplicationProps
) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const leaveStartDate = formatDate(claim.leaveStartDate).full();
  const otherLeaveStartDate = formatDate(
    claim.computed_start_dates.other_reason
  ).full();

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
        label={
          <Heading level="2" size="1">
            {t("pages.claimsPreviousLeavesOtherReason.sectionLabel", {
              leaveStartDate,
              otherLeaveStartDate,
            })}
          </Heading>
        }
        hint={
          <React.Fragment>
            <Heading level="3">
              <Icon
                name="check"
                size={3}
                className="text-secondary text-middle margin-right-1 margin-top-neg-05"
              />
              {t("pages.claimsPreviousLeavesOtherReason.hintDoHeader")}
            </Heading>
            <Trans
              i18nKey="pages.claimsPreviousLeavesOtherReason.hintList"
              components={{
                ul: <ul className="usa-list margin-left-4" />,
                li: <li />,
              }}
            />
            <Heading level="3">
              <Icon
                name="close"
                size={3}
                className="text-error text-middle margin-right-1 margin-top-neg-05"
              />
              {t("pages.claimsPreviousLeavesOtherReason.hintDontHeader")}
            </Heading>
            <Trans
              i18nKey="pages.claimsPreviousLeavesOtherReason.leaveTakenThroughPFML"
              components={{
                ul: <ul className="usa-list margin-left-4" />,
                li: <li />,
              }}
            />
          </React.Fragment>
        }
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(PreviousLeavesOtherReason);
