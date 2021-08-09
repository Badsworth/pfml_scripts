import React, { useEffect, useState } from "react";

import Alert from "../../components/Alert";
import AppErrorInfo from "../../models/AppErrorInfo";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import BenefitsApplication from "../../models/BenefitsApplication";
import ComboBox from "../../components/ComboBox";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../../components/Details";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
// import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.org_unit"];

const allDepartments = [
  {
    department_id: 1,
    reporting_unit_description: "HR",
  },
  {
    department_id: 2,
    reporting_unit_description: "DFML",
  },
  {
    department_id: 3,
    reporting_unit_description: "Contact Center",
  },
  {
    department_id: 4,
    reporting_unit_description: "DevOps",
  },
  {
    department_id: 5,
    reporting_unit_description: "DevOps2",
  },
  {
    department_id: 6,
    reporting_unit_description: "DevOps3",
  },
];

export const Department = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  // const showDepartments = isFeatureEnabled("claimantShowDepartments");

  const initialFormState = pick(props, fields).claim;

  const { formState, updateFields, getField, clearField } =
    useFormState(initialFormState);

  // if (!showDepartments) {
  // @todo: go to next page and ignore departments, auto-select "I'm not sure"
  // }

  const [departments, setDepartments] = useState([]);
  const [employerDepartments, setEmployerDepartments] = useState([]);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const workarounds = [
    t("pages.claimsDepartment.choiceNotListed"),
    t("pages.claimsDepartment.choiceNotSure"),
  ];
  const hasSelectedRadioWorkaround = [...workarounds, "No"].includes(
    formState.org_unit_radio
  );
  const hasSelectedComboboxWorkaround = workarounds.includes(
    formState.org_unit
  );

  // API calls
  const handleSave = () => {
    // If user selects a workaround, then take the combobox's value
    // otherwise, take the radio group's value
    const errors = [];

    const finalDepartmentDecision = hasSelectedRadioWorkaround
      ? formState.org_unit
      : formState.org_unit_radio;

    formState.org_unit = finalDepartmentDecision;

    if (isUnique && !formState.org_unit_radio) {
      const noConfirmationError = new AppErrorInfo({
        field: "org_unit_radio",
        message: t("pages.claimsDepartment.errors.missingConfirmation"),
        type: "required",
      });

      errors.push(noConfirmationError);
    }
    if (
      (isShort && !formState.org_unit_radio) ||
      (isLong && !formState.org_unit) ||
      (!isLong && formState.org_unit_radio && !formState.org_unit)
    ) {
      const missingDepartmentError = new AppErrorInfo({
        field:
          isShort && !formState.org_unit_radio ? "org_unit_radio" : "org_unit",
        message: t("pages.claimsDepartment.errors.missingDepartment"),
        type: "required",
      });

      errors.push(missingDepartmentError);
    }

    appLogic.setAppErrors(new AppErrorInfoCollection(errors));

    console.log("Selected", finalDepartmentDecision);

    if (errors.length > 0) return;

    delete formState.org_unit_radio;
    formState.org_unit = finalDepartmentDecision;

    appLogic.benefitsApplications.update(claim.application_id, formState);
  };

  const populateDepartments = async () => {
    let claimantDeps = [];
    let employerDeps = [];
    // obtain the full list of departments connected to this claimant
    if (!departments.length) {
      const employee = await appLogic.employees.search({
        first_name: claim.first_name,
        last_name: claim.last_name,
        middle_name: claim.middle_name ?? "",
        tax_identifier_last4: claim.tax_identifier.slice(-4),
      });
      console.log(
        { employee },
        {
          first_name: claim.first_name,
          last_name: claim.last_name,
          middle_name: claim.middle_name ?? "",
          tax_identifier_last4: claim.tax_identifier.slice(-4),
        }
      );
      if (employee) claimantDeps = employee.reporting_units;
    }
    // obtain the full list of departments connected to this claimant's employer
    if (!employerDepartments.length) {
      // const deps = await appLogic.benefitsApplications.getDepartmentsByEmployer(claim.employer_fein)
      employerDeps = await allDepartments;
    }

    setDepartments(claimantDeps.length ? claimantDeps : employerDeps);
    setEmployerDepartments(employerDeps);
  };

  // Helpers
  const getDepartmentListSizes = (deps) => {
    const isLong = deps.length > 5;
    const isShort = deps.length > 1 && deps.length <= 5;
    const isUnique = deps.length === 1;
    return {
      isLong,
      isShort,
      isUnique,
    };
  };

  const getDepartmentChoices = (deps) => {
    if (!deps.length) return [];

    const { isLong, isShort, isUnique } = getDepartmentListSizes(deps);

    const departmentChoices = deps.map((dep) => ({
      label: dep.reporting_unit_description,
      value: dep.reporting_unit_description,
      checked: dep.reporting_unit_description === formState.org_unit_radio,
    }));

    // @todo: value cannot be a translated label text
    const workaroundChoices = workarounds.map((wa) => ({
      label: wa,
      value: wa,
      checked: wa === formState.org_unit_radio,
    }));

    if (isLong || isShort) {
      return [...departmentChoices, ...workaroundChoices];
    }
    if (isUnique) {
      const firstDep = deps[0]?.reporting_unit_description;
      return [
        {
          label: t("pages.claimsDepartment.choiceYes"),
          value: firstDep,
          checked: formState.org_unit_radio === firstDep,
        },
        {
          label: t("pages.claimsDepartment.choiceNo"),
          value: "No",
          checked: formState.org_unit_radio === "No",
        },
      ];
    }
  };

  const { isLong, isShort, isUnique } = getDepartmentListSizes(departments);
  const claimantChoices = getDepartmentChoices(departments);
  const employerChoices = getDepartmentChoices(employerDepartments);

  useEffect(() => {
    // lazy loads both departments lists into state
    populateDepartments();
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (isLong || !departments.length) return () => null;
    // sets radio options to the first workaround option
    // when the claim org_unit is not one of the radio options shown
    // and is instead selected in the combo box component
    updateFields({
      ...initialFormState,
      org_unit_radio:
        claimantChoices.length && initialFormState.org_unit
          ? claimantChoices.find((c) => c.value === initialFormState.org_unit)
            ? initialFormState.org_unit
            : isUnique
            ? "No"
            : workarounds[0]
          : null,
    });
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [departments]);

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <ConditionalContent visible={isUnique}>
        <InputChoiceGroup
          {...getFunctionalInputProps("org_unit_radio")}
          choices={claimantChoices}
          label={t("pages.claimsDepartment.confirmSectionLabel")}
          hint={
            <React.Fragment>
              <Trans
                i18nKey="pages.claimsDepartment.confirmHint"
                tOptions={{
                  department: departments[0]?.reporting_unit_description,
                }}
              />
              <div className="margin-top-2">
                <Details label={t("pages.claimsDepartment.moreThanOne")}>
                  {t("pages.claimsDepartment.hint")}
                </Details>
              </div>
            </React.Fragment>
          }
          type="radio"
        />
      </ConditionalContent>

      <ConditionalContent visible={isShort}>
        <InputChoiceGroup
          {...getFunctionalInputProps("org_unit_radio", {
            fallbackValue: formState.org_unit_radio || "",
          })}
          choices={claimantChoices}
          label={t("pages.claimsDepartment.sectionLabel")}
          hint={t("pages.claimsDepartment.hint")}
          type="radio"
        />
      </ConditionalContent>

      <ConditionalContent
        visible={isLong || hasSelectedRadioWorkaround}
        fieldNamesClearedWhenHidden={["org_unit"]}
        updateFields={updateFields}
        clearField={clearField}
        getField={getField}
      >
        <Fieldset>
          <ConditionalContent visible={isLong}>
            <FormLabel
              component="legend"
              hint={t("pages.claimsDepartment.hint")}
            >
              {t("pages.claimsDepartment.sectionLabel")}
            </FormLabel>
          </ConditionalContent>
          <ComboBox
            {...getFunctionalInputProps("org_unit", {
              fallbackValue: formState.org_unit || "",
            })}
            choices={
              hasSelectedRadioWorkaround ? employerChoices : claimantChoices
            }
            label={t("pages.claimsDepartment.comboBoxLabel")}
            smallLabel
            required
          />
          <ConditionalContent visible={hasSelectedComboboxWorkaround}>
            <Alert className="measure-6" state="info" slim>
              {t("pages.claimsDepartment.followupInfo")}
            </Alert>
          </ConditionalContent>
        </Fieldset>
      </ConditionalContent>
    </QuestionPage>
  );
};

Department.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(Department);
