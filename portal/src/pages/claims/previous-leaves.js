import Claim from "../../models/Claim";
import Details from "../../components/Details";
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

export const fields = ["claim.has_previous_leaves"];

export const PreviousLeaves = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const { has_previous_leaves } = formState;

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });
  const hintList = t("pages.claimsPreviousLeaves.hintList", {
    returnObjects: true,
  });

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeaves.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_previous_leaves")}
        choices={[
          {
            checked: has_previous_leaves === true,
            label: t("pages.claimsPreviousLeaves.choiceYes"),
            value: "true",
          },
          {
            checked: has_previous_leaves === false,
            label: t("pages.claimsPreviousLeaves.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsPreviousLeaves.sectionLabel")}
        type="radio"
        hint={
          <Details label={t("pages.claimsPreviousLeaves.detailsLabel")}>
            <React.Fragment>
              <Lead>{t("pages.claimsPreviousLeaves.hintHeader")}</Lead>
              <ul className="usa-list">
                {hintList.map((listItem, index) => (
                  <li key={index}>{listItem}</li>
                ))}
              </ul>
            </React.Fragment>
          </Details>
        }
      />
    </QuestionPage>
  );
};

PreviousLeaves.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};
export default withClaim(PreviousLeaves);
