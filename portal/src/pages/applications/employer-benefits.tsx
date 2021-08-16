import BenefitsApplication from "../../models/BenefitsApplication";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
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
  const hintList = t("pages.claimsEmployerBenefits.hintList", {
    returnObjects: true,
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
            value: "true",
          },
          {
            checked: formState.has_employer_benefits === false,
            label: t("pages.claimsEmployerBenefits.choiceNo"),
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
            <p>{t("pages.claimsEmployerBenefits.hintHeader")}</p>
            <ul className="usa-list">
              {/* @ts-expect-error ts-migrate(2339) FIXME: Property 'map' does not exist on type 'string'. */}
              {hintList.map((listItem, index) => (
                <li key={index}>{listItem}</li>
              ))}
            </ul>
            <Trans
              i18nKey="pages.claimsEmployerBenefits.hintBody"
              tOptions={{ employer_fein }}
            />
          </React.Fragment>
        }
      />
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
