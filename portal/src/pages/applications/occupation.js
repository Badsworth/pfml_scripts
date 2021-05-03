import BenefitsApplication from "../../models/BenefitsApplication";
import Dropdown from "../../components/Dropdown";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import StateDropdown from "../../components/StateDropdown";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.occupation", "claim.occupationTitle"];

export const Occupation = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage title={t("pages.claimsOccupation.title")} onSave={handleSave}>
      <Fieldset>
        <Dropdown
          {...getFunctionalInputProps("occupation")}
          choices={[
            {
              label: "Clothing",
              value: "Clothing",
            },
            {
              label: "Mining",
              value: "Mining",
            },
            {
              label: "Agriculture",
              value: "Agriculture",
            },
          ]}
          label={t("pages.claimsOccupation.occupation_label")}
          emptyChoiceLabel="- Select an answer -"
          smallLabel
        />
        <Dropdown
          {...getFunctionalInputProps("occupation_title")}
          choices={[
            {
              label: "Hat-making",
              value: "Hat-making",
            },
            {
              label: "Boot-making",
              value: "Boot-making",
            },
            {
              label: "Scarf-making",
              value: "Scarf-making",
            },
          ]}
          label={t("pages.claimsOccupation.occupation_title_label")}
          emptyChoiceLabel="- Select an answer -"
          smallLabel
        />
      </Fieldset>
    </QuestionPage>
  );
};

Occupation.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(Occupation);
