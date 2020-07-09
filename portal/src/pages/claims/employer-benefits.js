import Claim from "../../models/Claim";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.has_employer_benefits"];

export const EmployerBenefits = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const { has_employer_benefits } = formState;
  const handleInputChange = useHandleInputChange(updateFields);
  const benefitList = t("pages.claimsEmployerBenefits.detailsList", {
    returnObjects: true,
  });

  const handleSave = () =>
    props.appLogic.updateClaim(props.claim.application_id, formState);

  return (
    <QuestionPage
      title={t("pages.claimsEmployerBenefits.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: has_employer_benefits === true,
            label: t("pages.claimsEmployerBenefits.choiceYes"),
            value: "true",
          },
          {
            checked: has_employer_benefits === false,
            label: t("pages.claimsEmployerBenefits.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsEmployerBenefits.sectionLabel")}
        name="has_employer_benefits"
        onChange={handleInputChange}
        type="radio"
        hint={
          <React.Fragment>
            <Lead>{t("pages.claimsEmployerBenefits.detailsHeader")}</Lead>
            <ul className="usa-list">
              {benefitList.map((listItem, index) => (
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
