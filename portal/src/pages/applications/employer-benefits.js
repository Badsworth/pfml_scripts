import Claim from "../../models/Claim";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.has_employer_benefits"];

export const EmployerBenefits = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () => {
    if (
      formState.has_employer_benefits === false &&
      claim.employer_benefits.length
    ) {
      formState.employer_benefits = null;
    }
    appLogic.claims.update(claim.application_id, formState);
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

EmployerBenefits.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(EmployerBenefits);
