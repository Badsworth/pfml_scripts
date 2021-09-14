import React, { useEffect, useState } from "react";

import Alert from "../../components/Alert";
import AppErrorInfo from "../../models/AppErrorInfo";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import BenefitsApplication from "../../models/BenefitsApplication";
import ComboBox from "../../components/ComboBox";
import ConditionalContent from "../../components/ConditionalContent";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.reporting_unit"];

export const Department = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const showDepartments = isFeatureEnabled("claimantShowDepartments");

  const initialFormState = pick(props, fields).claim;

  const { formState, updateFields, getField, clearField } =
    useFormState(initialFormState);

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
    formState.radio_reporting_unit
  );
  const hasSelectedComboboxWorkaround = workarounds.includes(
    formState.reporting_unit
  );

  // API calls
  const handleSave = () => {
    // If user selects a workaround, then take the combobox's value
    // otherwise, take the radio group's value
    const errors = [];

    const finalDepartmentDecision =
      hasSelectedRadioWorkaround || isLong
        ? formState.reporting_unit
        : formState.radio_reporting_unit;

    formState.reporting_unit = finalDepartmentDecision;

    if (isUnique && !formState.radio_reporting_unit) {
      const noConfirmationError = new AppErrorInfo({
        field: "radio_reporting_unit",
        message: t("pages.claimsDepartment.errors.missingConfirmation"),
        type: "required",
      });

      errors.push(noConfirmationError);
    }
    if (
      (isShort && !formState.radio_reporting_unit) ||
      (isLong && !formState.reporting_unit) ||
      (!isLong && formState.radio_reporting_unit && !formState.reporting_unit)
    ) {
      const missingDepartmentError = new AppErrorInfo({
        field:
          isShort && !formState.radio_reporting_unit
            ? "radio_reporting_unit"
            : "reporting_unit",
        message: t("pages.claimsDepartment.errors.missingDepartment"),
        type: "required",
      });

      errors.push(missingDepartmentError);
    }

    appLogic.setAppErrors(new AppErrorInfoCollection(errors));

    if (errors.length > 0) return;

    delete formState.radio_reporting_unit;
    formState.reporting_unit = finalDepartmentDecision;

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
      if (employee) claimantDeps = employee.reporting_units;
    }
    // obtain the full list of departments connected to this claimant's employer
    if (!employerDepartments.length) {
      // const deps = await appLogic.benefitsApplications.getDepartmentsByEmployer(claim.employer_fein)
      // employerDeps = [];
      employerDeps = [...claimantDeps].slice(1);
    }
    // claimantDeps = claimantDeps.slice(0, 1);

    setDepartments(claimantDeps?.length ? claimantDeps : employerDeps);
    setEmployerDepartments(employerDeps);
  };

  // Helpers
  const getDepartmentListSizes = (deps) => {
    const isLong = deps.length > 3;
    const isShort = deps.length > 1 && deps.length <= 3;
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
      checked:
        dep.reporting_unit_description === formState.radio_reporting_unit,
    }));

    // @todo: value cannot be a translated label text
    const workaroundChoices = workarounds.map((wa) => ({
      label: wa,
      value: wa,
      checked: wa === formState.radio_reporting_unit,
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
          checked: formState.radio_reporting_unit === firstDep,
        },
        {
          label: t("pages.claimsDepartment.choiceNo"),
          value: "No",
          checked: formState.radio_reporting_unit === "No",
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
    // when the claim reporting_unit_id is not one of the radio options shown
    // and is instead selected in the combo box component
    updateFields({
      ...initialFormState,
      radio_reporting_unit:
        claimantChoices.length && initialFormState.reporting_unit
          ? claimantChoices.find(
              (c) => c.value === initialFormState.reporting_unit
            )
            ? initialFormState.reporting_unit
            : isUnique
            ? "No"
            : workarounds[0]
          : null,
    });
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [departments]);

  if (!showDepartments) {
    // @todo: go to next page and ignore departments, auto-select "I'm not sure"
    appLogic.portalFlow.goTo(routes.applications.notifiedEmployer, {
      claim_id: claim.application_id,
    });
  }

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <ConditionalContent visible={isUnique}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_reporting_unit")}
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
              {/* <div className="margin-top-2">
                <http://localhost:3000/img/usa-icons/chevrons.svgDetails label={t("pages.claimsDepartment.moreThanOne")}>
                  {t("pages.claimsDepartment.hint")}
                </Details>
              </div> */}
            </React.Fragment>
          }
          type="radio"
        />
      </ConditionalContent>

      <ConditionalContent visible={isShort}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_reporting_unit", {
            fallbackValue: formState.radio_reporting_unit || "",
          })}
          choices={claimantChoices}
          label={t("pages.claimsDepartment.sectionLabel")}
          // hint={t("pages.claimsDepartment.hint")}
          type="radio"
        />
      </ConditionalContent>

      <ConditionalContent
        visible={isLong || hasSelectedRadioWorkaround}
        fieldNamesClearedWhenHidden={["reporting_unit"]}
        updateFields={updateFields}
        clearField={clearField}
        getField={getField}
      >
        <Fieldset>
          <ConditionalContent visible={isLong}>
            <FormLabel
              component="legend"
              // hint={t("pages.claimsDepartment.hint")}
            >
              {t("pages.claimsDepartment.sectionLabel")}
            </FormLabel>
          </ConditionalContent>
          <ConditionalContent visible={showDepartments}>
            <ComboBox
              {...getFunctionalInputProps("reporting_unit", {
                fallbackValue: formState.reporting_unit || "",
              })}
              choices={
                hasSelectedRadioWorkaround ? employerChoices : claimantChoices
              }
              label={t("pages.claimsDepartment.comboBoxLabel")}
              smallLabel
              required
            />
          </ConditionalContent>
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
