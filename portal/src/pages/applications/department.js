import React, { useEffect, useState } from "react";

import Alert from "../../components/Alert";
import BenefitsApplication from "../../models/BenefitsApplication";
import ComboBox from "../../components/ComboBox";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
// import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.org_unit"];

export const Department = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  // const showDepartments = isFeatureEnabled("claimantShowDepartments");

  const initialFormState = pick(props, fields).claim;

  // if (!showDepartments) {
  // @todo: go to next page and ignore departments, auto-select "I'm not sure"
  // }

  const { formState, updateFields } = useFormState(initialFormState);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const [departments, setDepartments] = useState([]);
  const otherOptions = [
    t("pages.claimsDepartment.choiceNotListed"),
    t("pages.claimsDepartment.choiceNotSure"),
  ];
  const populateDepartments = () => {
    // const occupationOptions = await appLogic.benefitsApplications.getDepartments();
    const departmentOptions = [
      {
        department_id: 1,
        department_description: "HR",
      },
      {
        department_id: 2,
        department_description: "DFML",
      },
      {
        department_id: 3,
        department_description: "Contact Center",
      },
      {
        department_id: 4,
        department_description: "DevOps",
      },
    ];
    setDepartments([
      ...departmentOptions.map((department) => ({
        label: department.department_description,
        value: department.department_description,
        // checked: department.department_description === formState.org_unit
      })),
      ...otherOptions.map((department) => ({
        label: department,
        value: department,
        // checked: department === formState.org_unit
      })),
    ]);
  };

  const isLongList = departments.length > 5;
  const isSmallList = departments.length > 1 && departments.length <= 5;
  // const isUnique = departments.length === 1;
  const isOtherOptionSelected = otherOptions.includes(formState.org_unit);

  useEffect(() => {
    populateDepartments();
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      {isSmallList && (
        <React.Fragment>
          <InputChoiceGroup
            {...getFunctionalInputProps("org_unit")}
            choices={departments}
            label={t("pages.claimsDepartment.sectionLabel")}
            hint={t("pages.claimsDepartment.hint")}
            type="radio"
          />
        </React.Fragment>
      )}
      {(isLongList || (isSmallList && isOtherOptionSelected)) && (
        <React.Fragment>
          <Fieldset>
            {!isSmallList && (
              <FormLabel
                component="legend"
                hint={t("pages.claimsDepartment.hint")}
              >
                {t("pages.claimsDepartment.sectionLabel")}
              </FormLabel>
            )}
            <ComboBox
              {...getFunctionalInputProps("org_unit")}
              choices={departments}
              label={t("pages.claimsDepartment.comboBoxLabel")}
              smallLabel
            />
            {isOtherOptionSelected && (
              <Alert className="measure-6" state="info" noIcon>
                {t("pages.claimsDepartment.followupInfo")}
              </Alert>
            )}
          </Fieldset>
        </React.Fragment>
      )}
    </QuestionPage>
  );
};

Department.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(Department);
