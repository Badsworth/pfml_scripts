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

export const fields = ["claim.temp.has_other_incomes"];

export const OtherIncomes = (props) => {
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
  const hintList = t("pages.claimsOtherIncomes.hintList", {
    returnObjects: true,
  });

  return (
    <QuestionPage
      title={t("pages.claimsOtherIncomes.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("temp.has_other_incomes")}
        choices={[
          {
            checked: formState.temp.has_other_incomes === true,
            label: t("pages.claimsOtherIncomes.choiceYes"),
            value: "true",
          },
          {
            checked: formState.temp.has_other_incomes === false,
            label: t("pages.claimsOtherIncomes.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsOtherIncomes.sectionLabel")}
        type="radio"
        hint={
          <React.Fragment>
            <Lead>
              {t("pages.claimsOtherIncomes.hintHeader")}
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

OtherIncomes.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(OtherIncomes);
