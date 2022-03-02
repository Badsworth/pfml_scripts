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
import { Trans } from "react-i18next";
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
    errors: appLogic.errors,
    formState,
    updateFields,
  });

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
        label={
          <Heading level="2" size="1">
            {t("pages.claimsOtherIncomes.sectionLabel")}
          </Heading>
        }
        type="radio"
        hint={
          <React.Fragment>
            <LeaveDatesAlert
              startDate={claim.leaveStartDate}
              endDate={claim.leaveEndDate}
            />
            <Heading level="3">
              <Icon
                name="check"
                size={3}
                className="text-secondary text-middle margin-right-1 margin-top-neg-05"
              />
              {t("pages.claimsOtherIncomes.doReportHintHeading")}
            </Heading>
            <Trans
              i18nKey="pages.claimsOtherIncomes.doReportHintList"
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
              {t("pages.claimsOtherIncomes.doNotReportHintHeading")}
            </Heading>
            <Trans
              i18nKey="pages.claimsOtherIncomes.doNotReportHintList"
              components={{
                ul: <ul className="usa-list margin-left-4" />,
                li: <li />,
              }}
            />
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
