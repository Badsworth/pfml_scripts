import Claim from "../../models/Claim";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.has_employer_benefits"];

const EmployerBenefits = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

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
            <Lead>
              {t("pages.claimsEmployerBenefits.hintHeader")}
              <ul className="usa-list">
                {hintList.map((listItem, index) => (
                  <li key={index}>{listItem}</li>
                ))}
              </ul>
            </Lead>
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
