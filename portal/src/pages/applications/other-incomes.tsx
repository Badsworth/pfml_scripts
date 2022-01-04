import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Alert from "../../components/core/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Heading from "../../components/core/Heading";
import Icon from "../../components/core/Icon";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.has_other_incomes"];

export const OtherIncomes = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () => {
    if (formState.has_other_incomes === false && claim.other_incomes.length) {
      formState.other_incomes = null;
    }
    return appLogic.benefitsApplications.update(
      claim.application_id,
      formState
    );
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });
  const doReportHintList = t<string, string[]>(
    "pages.claimsOtherIncomes.doReportHintList",
    {
      returnObjects: true,
    }
  );
  const doNotReportHintList = t<string, string[]>(
    "pages.claimsOtherIncomes.doNotReportHintList",
    {
      returnObjects: true,
    }
  );

  return (
    <QuestionPage
      title={t("pages.claimsOtherIncomes.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_other_incomes")}
        choices={[
          {
            checked: formState.has_other_incomes === true,
            label: t("pages.claimsOtherIncomes.choiceYes"),
            hint: t("pages.claimsOtherIncomes.choiceYesHint"),
            value: "true",
          },
          {
            checked: formState.has_other_incomes === false,
            label: t("pages.claimsOtherIncomes.choiceNo"),
            hint: t("pages.claimsOtherIncomes.choiceNoHint"),
            value: "false",
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
            <Heading level="2" size="3">
              <Icon
                name="check_circle"
                size={3}
                className="text-secondary text-middle margin-right-05 margin-top-neg-05"
                fill="currentColor"
              />
              {t("pages.claimsOtherIncomes.doReportHintHeading")}
            </Heading>
            <ul className="usa-list margin-top-0 margin-left-4 margin-bottom-4">
              {doReportHintList.map((listItem, index) => (
                <li key={index}>{listItem}</li>
              ))}
            </ul>
            <Heading level="2" size="3">
              <Icon
                name="cancel"
                size={3}
                className="text-error text-middle margin-right-05 margin-top-neg-05"
                fill="currentColor"
              />
              {t("pages.claimsOtherIncomes.doNotReportHintHeading")}
            </Heading>
            <ul className="usa-list margin-top-0 margin-left-4">
              {doNotReportHintList.map((listItem, index) => (
                <li key={index}>{listItem}</li>
              ))}
            </ul>
          </React.Fragment>
        }
      />
      <ConditionalContent visible={formState.has_other_incomes === false}>
        <Alert state="info" role="alert" slim>
          {t("pages.claimsOtherIncomes.choiceNoAlert")}
        </Alert>
      </ConditionalContent>
    </QuestionPage>
  );
};

export default withBenefitsApplication(OtherIncomes);
