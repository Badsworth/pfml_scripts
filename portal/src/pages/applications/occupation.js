import React, { useEffect, useState } from "react";

import BenefitsApplication from "../../models/BenefitsApplication";
import Dropdown from "../../components/Dropdown";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [
  "claim.occupation_id",
  "claim.occupation_title_id",
  "claim.occupation_title_custom",
];

export const AppOccupation = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const showOccupation = isFeatureEnabled("claimantShowOccupation");

  const initialFormState = pick(props, fields).claim;

  if (!showOccupation) {
    // @todo: If the radio buttons are disabled, hard-code the field so that validations pass
  }

  const { formState, getField, updateFields, clearField } = useFormState(
    initialFormState
  );
  const occupation_id = getField("occupation_id");

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const occupationDefaults = [
    {
      label: t("pages.claimsOccupation.selectCategory"),
      value: 0,
    },
    {
      label: t("pages.claimsOccupation.notListed"),
      value: -1,
    },
  ];
  const occupationTitleDefaults = [
    {
      label: t("pages.claimsOccupation.selectOption"),
      value: 0,
    },
  ];
  const [occupations, setOccupations] = useState(occupationDefaults);
  const [occupationTitles, setOccupationTitles] = useState(
    occupationTitleDefaults
  );
  const populateOccupations = async () => {
    setOccupations([
      ...occupationDefaults.filter((d) => d.value !== -1),
      ...(await appLogic.benefitsApplications.getOccupations()).map(
        (occupation) => ({
          label: occupation.occupation_description,
          value: occupation.occupation_id,
        })
      ),
      occupationDefaults.find((d) => d.value === -1),
    ]);
  };
  const populateTitles = async (event) => {
    const { name, value } = event.target;
    if (value > 0) {
      setOccupationTitles([
        ...occupationTitleDefaults,
        ...(await appLogic.benefitsApplications.getOccupationTitles(value)).map(
          (title) => ({
            label: title.occupation_title_description,
            value: title.occupation_title_id,
          })
        ),
      ]);
      clearField("occupation_title_custom");
    } else {
      clearField("occupation_title_id");
    }
    // updates occupation category
    updateFields({ [name]: value });
  };

  useEffect(() => {
    populateOccupations();
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <QuestionPage title={t("pages.claimsOccupation.title")} onSave={handleSave}>
      <Dropdown
        {...getFunctionalInputProps(`occupation_id`)}
        onChange={populateTitles}
        choices={occupations}
        label="Occupation"
        labelClassName="text-normal margin-top-0"
        formGroupClassName="margin-top-1"
        hideEmptyChoice
        smallLabel
      />
      <Dropdown
        {...getFunctionalInputProps(`occupation_title_id`)}
        choices={occupationTitles}
        label="Occupation Title"
        labelClassName="text-normal margin-top-0"
        formGroupClassName="margin-top-1"
        hideEmptyChoice
        smallLabel
        disabled={parseInt(occupation_id) < 1}
      />
      <InputText
        {...getFunctionalInputProps("occupation_title_custom")}
        label="Custom occupation title"
        smallLabel
        maxLength="255"
        disabled={parseInt(occupation_id) !== -1}
      />
    </QuestionPage>
  );
};

AppOccupation.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(AppOccupation);
