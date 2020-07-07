import Claim, { EmploymentStatus } from "../../models/Claim";
import Alert from "../../components/Alert";
import Details from "../../components/Details";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import get from "lodash/get";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["leave_details.employment_status"];

export const EmploymentStatusPage = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const { formState, updateFields } = useFormState(pick(claim, fields));
  const employment_status = get(formState, "leave_details.employment_status");
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = () => {
    appLogic.updateClaim(claim.application_id, formState);
  };

  return (
    <QuestionPage
      formState={formState}
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
        name="leave_details.employment_status"
        onChange={handleInputChange}
        type="radio"
      />
    </QuestionPage>
  );
};

EmploymentStatusPage.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
  appLogic: PropTypes.shape({
    updateClaim: PropTypes.func.isRequired,
  }).isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }).isRequired,
};

export default withClaim(EmploymentStatusPage);
