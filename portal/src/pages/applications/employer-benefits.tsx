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

export const fields = ["claim.has_employer_benefits"];

export const EmployerBenefits = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const employer_fein = claim.employer_fein;

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () => {
    if (
      formState.has_employer_benefits === false &&
      claim.employer_benefits.length
    ) {
      formState.employer_benefits = null;
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
      title={t("pages.claimsEmployerBenefits.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_employer_benefits")}
        choices={[
          {
            checked: formState.has_employer_benefits === true,
            label: t("pages.claimsEmployerBenefits.choiceYes"),
            hint: t("pages.claimsEmployerBenefits.choiceYesHint"),
            value: "true",
          },
          {
            checked: formState.has_employer_benefits === false,
            label: t("pages.claimsEmployerBenefits.choiceNo"),
            hint: t("pages.claimsEmployerBenefits.choiceNoHint"),
            value: "false",
          },
        ]}
        label={t("pages.claimsEmployerBenefits.sectionLabel")}
        type="radio"
        hint={
          <React.Fragment>
            <LeaveDatesAlert
              startDate={claim.leaveStartDate}
              endDate={claim.leaveEndDate}
            />
            <Heading level="2" size="3">
              <Icon
                name="check"
                size={3}
                className="text-secondary text-middle margin-right-05 margin-top-neg-05"
                fill="currentColor"
              />
              {t("pages.claimsEmployerBenefits.doReportHintHeading")}
            </Heading>
            <div className="margin-left-4">
              <Trans
                i18nKey="pages.claimsEmployerBenefits.doReportHintList"
                tOptions={{ employer_fein }}
                components={{
                  ul: <ul className="usa-list" />,
                  li: <li />,
                }}
              />
            </div>
            <Heading level="2" size="3">
              <Icon
                name="close"
                size={3}
                className="text-error text-middle margin-right-05 margin-top-neg-05"
                fill="currentColor"
              />
              {t("pages.claimsEmployerBenefits.doNotReportHintHeading")}
            </Heading>
            <div className="margin-left-4">
              <Trans
                i18nKey="pages.claimsEmployerBenefits.doNotReportHintList"
                components={{
                  ul: <ul className="usa-list" />,
                  li: <li />,
                }}
              />
            </div>
          </React.Fragment>
        }
      />
      <ConditionalContent visible={formState.has_employer_benefits === false}>
        <Alert state="info" role="alert" slim>
          {t("pages.claimsEmployerBenefits.choiceNoAlert")}
        </Alert>
      </ConditionalContent>
    </QuestionPage>
  );
};

export default withBenefitsApplication(EmployerBenefits);
