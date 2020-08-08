import Claim, { EmploymentStatus } from "../../models/Claim";
import { get, pick } from "lodash";
import Alert from "../../components/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../../components/Details";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.employment_status", "claim.employer_fein"];

const EmploymentStatusPage = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const { formState, getField, updateFields, removeField } = useFormState(
    pick(props, fields).claim
  );
  const employment_status = get(formState, "employment_status");
  const employer_fein = get(formState, "employer_fein");
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = () => {
    appLogic.claims.update(claim.application_id, formState);
  };

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <Alert state="info">
        {t("pages.claimsEmploymentStatus.multipleEmployerAppAlert")}
      </Alert>

      <InputChoiceGroup
        choices={["employed", "unemployed", "selfEmployed"].map((key) => ({
          checked: employment_status === EmploymentStatus[key],
          label: t("pages.claimsEmploymentStatus.choiceLabel", {
            context: key,
          }),
          value: EmploymentStatus[key],
        }))}
        label={t("pages.claimsEmploymentStatus.sectionLabel")}
        hint={
          <Details label={t("pages.claimsEmploymentStatus.furloughQuestion")}>
            {t("pages.claimsEmploymentStatus.furloughAnswer")}
          </Details>
        }
        name="employment_status"
        onChange={handleInputChange}
        type="radio"
      />
      <ConditionalContent
        fieldNamesClearedWhenHidden={["employer_fein"]}
        getField={getField}
        removeField={removeField}
        updateFields={updateFields}
        visible={employment_status === EmploymentStatus.employed}
      >
        <InputText
          type="numeric"
          name="employer_fein"
          label={t("pages.claimsEmploymentStatus.feinLabel")}
          mask="fein"
          hint={t("pages.claimsEmploymentStatus.feinHint")}
          value={valueWithFallback(employer_fein)}
          onChange={handleInputChange}
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

EmploymentStatusPage.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
  appLogic: PropTypes.shape({
    claims: {
      update: PropTypes.func.isRequired,
    },
  }).isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }).isRequired,
};

export default withClaim(EmploymentStatusPage);
