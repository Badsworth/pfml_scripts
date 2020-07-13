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

export const fields = ["claim.has_other_incomes"];

const OtherIncomes = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const { has_other_incomes } = formState;
  const handleInputChange = useHandleInputChange(updateFields);
  const hintList = t("pages.claimsOtherIncomes.hintList", {
    returnObjects: true,
  });

  const handleSave = () =>
    props.appLogic.updateClaim(props.claim.application_id, formState);

  return (
    <QuestionPage
      title={t("pages.claimsOtherIncomes.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: has_other_incomes === true,
            label: t("pages.claimsOtherIncomes.choiceYes"),
            value: "true",
          },
          {
            checked: has_other_incomes === false,
            label: t("pages.claimsOtherIncomes.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsOtherIncomes.sectionLabel")}
        name="has_other_incomes"
        onChange={handleInputChange}
        type="radio"
        hint={
          <React.Fragment>
            <Lead>{t("pages.claimsOtherIncomes.hintHeader")}</Lead>
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

OtherIncomes.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(OtherIncomes);
