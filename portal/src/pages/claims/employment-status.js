import Claim, {
  EmploymentStatus as EmploymentStatusEnum,
} from "../../models/Claim";
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
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.employment_status", "claim.employer_fein"];

export const EmploymentStatus = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );
  const employment_status = get(formState, "employment_status");

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <Alert state="info">
        {t("pages.claimsEmploymentStatus.multipleEmployerAppAlert")}
      </Alert>

      <InputChoiceGroup
        {...getFunctionalInputProps("employment_status")}
        choices={["employed", "unemployed", "selfEmployed"].map((key) => ({
          checked: employment_status === EmploymentStatusEnum[key],
          label: t("pages.claimsEmploymentStatus.choiceLabel", {
            context: key,
          }),
          value: EmploymentStatusEnum[key],
        }))}
        label={t("pages.claimsEmploymentStatus.sectionLabel")}
        hint={
          <Details label={t("pages.claimsEmploymentStatus.furloughQuestion")}>
            {t("pages.claimsEmploymentStatus.furloughAnswer")}
          </Details>
        }
        type="radio"
      />
      <ConditionalContent
        fieldNamesClearedWhenHidden={["employer_fein"]}
        getField={getField}
        clearField={clearField}
        updateFields={updateFields}
        visible={employment_status === EmploymentStatusEnum.employed}
      >
        <InputText
          {...getFunctionalInputProps("employer_fein")}
          type="numeric"
          label={t("pages.claimsEmploymentStatus.feinLabel")}
          mask="fein"
          hint={t("pages.claimsEmploymentStatus.feinHint")}
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

EmploymentStatus.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(Claim).isRequired,
};

export default withClaim(EmploymentStatus);
