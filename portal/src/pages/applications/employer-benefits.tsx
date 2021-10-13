import Alert from "../../components/Alert";
import BenefitsApplication from "../../models/BenefitsApplication";
import ConditionalContent from "../../components/ConditionalContent";
import Heading from "../../components/Heading";
import Icon from "../../components/Icon";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.has_employer_benefits"];

export const EmployerBenefits = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const employer_fein = claim.employer_fein;

  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
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
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });
  const doReportHintList = t<string, string[]>(
    "pages.claimsEmployerBenefits.doReportHintList",
    {
      returnObjects: true,
      employer_fein,
    }
  );
  const doNotReportHintList = t<string, string[]>(
    "pages.claimsEmployerBenefits.doNotReportHintList",
    {
      returnObjects: true,
    }
  );

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
            <Heading level="3">
              <Icon
                name="check_circle"
                size={3}
                className="text-secondary text-middle margin-right-05 margin-top-neg-05"
                fill="currentColor"
              />
              {t("pages.claimsEmployerBenefits.doReportHintHeading")}
            </Heading>
            <ul className="usa-list margin-top-0 margin-left-4 margin-bottom-4">
              {doReportHintList.map((listItem, index) => (
                <li key={index}>{listItem}</li>
              ))}
            </ul>
            <Heading level="3">
              <Icon
                name="cancel"
                size={3}
                className="text-error text-middle margin-right-05 margin-top-neg-05"
                fill="currentColor"
              />
              {t("pages.claimsEmployerBenefits.doNotReportHintHeading")}
            </Heading>
            <ul className="usa-list margin-top-0 margin-left-4">
              {doNotReportHintList.map((listItem, index) => (
                <li key={index}>{listItem}</li>
              ))}
            </ul>
          </React.Fragment>
        }
      />
      <ConditionalContent visible={formState.has_employer_benefits === false}>
        {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: string; state: string; role: str... Remove this comment to see the full error message */}
        <Alert state="info" role="alert" slim>
          {t("pages.claimsEmployerBenefits.choiceNoAlert")}
        </Alert>
      </ConditionalContent>
    </QuestionPage>
  );
};

EmployerBenefits.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withBenefitsApplication(EmployerBenefits);
