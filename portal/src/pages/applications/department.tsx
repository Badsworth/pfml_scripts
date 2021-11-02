import { DuaReportingUnit, OrganizationUnit } from "../../models/User";
import React, { useEffect, useState } from "react";

import Alert from "../../components/Alert";
import AppErrorInfo from "../../models/AppErrorInfo";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import { AppLogic } from "../../hooks/useAppLogic";
import BenefitsApplication from "../../models/BenefitsApplication";
import ComboBox from "../../components/ComboBox";
import ConditionalContent from "../../components/ConditionalContent";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import { NullableQueryParams } from "../../utils/routeWithParams";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.organization_unit_id"];

interface DepartmentProps {
  appLogic: AppLogic;
  claim: BenefitsApplication;
  query: NullableQueryParams;
}

interface CommonDepartment {
  id: string;
  name: string;
  type: "DUA" | "FINEOS" | "WORKAROUND";
}

export const Department = (props: DepartmentProps) => {
  const { appLogic, claim, query } = props;
  const { t } = useTranslation();

  const showDepartments = isFeatureEnabled("claimantShowDepartments");

  const initialFormState = pick(props, fields).claim;
  const { formState, updateFields, getField, clearField } =
    useFormState(initialFormState);

  const [departments, setDepartments] = useState<CommonDepartment[]>([]);
  const [employerDepartments, setEmployerDepartments] = useState<
    CommonDepartment[]
  >([]);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const NO: CommonDepartment = {
    id: "choiceNo",
    name: t("pages.claimsDepartment.choiceNo"),
    type: "WORKAROUND",
  };

  const NOT_LISTED: CommonDepartment = {
    id: "choiceNotListed",
    name: t("pages.claimsDepartment.choiceNotListed"),
    type: "WORKAROUND",
  };

  const NOT_SURE: CommonDepartment = {
    id: "choiceNotSure",
    name: t("pages.claimsDepartment.choiceNotSure"),
    type: "WORKAROUND",
  };

  // Determine whether user selected a "WORKAROUND" type option
  // while choosing from radio options
  const hasSelectedRadioWorkaround = !![NOT_LISTED, NOT_SURE, NO].find(
    (wa) => wa.id === formState.radio_organization_unit
  );
  // while choosing from comboBox options
  const hasSelectedComboboxWorkaround = !![NOT_LISTED, NOT_SURE].find(
    (wa) => wa.name === formState.organization_unit
  );

  // API calls
  const handleSave = async () => {
    const errors = [];

    // If user selects a workaround, then take the combobox's value
    // otherwise, take the radio group's value
    const finalDepartmentDecision =
      hasSelectedRadioWorkaround || isLong
        ? formState.organization_unit
        : formState.radio_organization_unit;

    formState.organization_unit = finalDepartmentDecision;

    if (isUnique && !formState.radio_organization_unit) {
      const noConfirmationError = new AppErrorInfo({
        field: "radio_organization_unit",
        message: t("pages.claimsDepartment.errors.missingConfirmation"),
        type: "required",
      });

      errors.push(noConfirmationError);
    }
    if (
      (isShort && !formState.radio_organization_unit) ||
      (isLong && !formState.organization_unit) ||
      (!isLong &&
        formState.radio_organization_unit &&
        !formState.organization_unit)
    ) {
      const missingDepartmentError = new AppErrorInfo({
        field:
          isShort && !formState.radio_organization_unit
            ? "radio_organization_unit"
            : "organization_unit_id",
        message: t("pages.claimsDepartment.errors.missingDepartment"),
        type: "required",
      });

      errors.push(missingDepartmentError);
    }

    appLogic.setAppErrors(new AppErrorInfoCollection(errors));

    if (errors.length > 0) return;

    formState.organization_unit_id = employerDepartmentOptions.find(
      (d) =>
        d.label === finalDepartmentDecision ||
        d.value === finalDepartmentDecision
    )?.value;
    delete formState.radio_organization_unit;
    delete formState.organization_unit;
    await appLogic.benefitsApplications.update(claim.application_id, formState);
  };

  const parseDepartments = (
    units: Array<DuaReportingUnit | OrganizationUnit>
  ): CommonDepartment[] => {
    // Converts DUA and FINEOS organization unit structures to a common type
    return units.map(
      (unit) =>
        ({
          id: unit.organization_unit_id,
          name:
            "dba" in unit
              ? (unit as DuaReportingUnit).dba
              : (unit as OrganizationUnit).name,
          type: "dba" in unit ? "DUA" : "FINEOS",
        } as CommonDepartment)
    );
  };

  const populateDepartments = async () => {
    // Finds this employee based on name, SSN and employer FEIN and retrieves 
    // the employee info alongside the connected DUA reporting units and 
    // this employer's list of organization units
    let claimantDeps: CommonDepartment[] = [];
    let employerDeps: CommonDepartment[] = [];
    // obtain the full list of departments connected to this claimant
    if (!departments.length) {
      const searchEmployee = {
        first_name: claim.first_name,
        last_name: claim.last_name,
        middle_name: claim.middle_name ?? "",
        tax_identifier_last4: claim.tax_identifier.slice(-4),
        employer_fein: claim.employer_fein,
      };
      const employee = await appLogic.employees.search(
        searchEmployee,
        claim.application_id
      );
      if (employee) {
        claimantDeps = parseDepartments(
          employee.connected_reporting_units || []
        );
        employerDeps = parseDepartments(employee.organization_units || []);
        /* 
        .filter(
            (o) =>
              o.organization_unit_id === "00472dec-687a-4f3f-97a8-2f611046c909" 
        )
        */
      } else {
        // very big problem
      }
    }

    setDepartments(claimantDeps.length ? claimantDeps : employerDeps);
    setEmployerDepartments(employerDeps);
  };

  // Helpers
  const getDepartmentListSizes = (deps: CommonDepartment[]) => {
    const isLong = deps.length > 3;
    const isShort = deps.length > 1 && deps.length <= 3;
    const isUnique = deps.length === 1;
    return {
      isLong,
      isShort,
      isUnique,
    };
  };

  const getDepartmentOptions = () => {
    // Construct radio and comboBox available department options
    const departmentOptions = departments.map((dep) => ({
      label: dep.name,
      value: dep.id,
      checked: dep.id === formState.radio_organization_unit,
    }));

    const employerDepartmentOptions = employerDepartments.map((dep) => ({
      label: dep.name,
      value: dep.id,
      checked: dep.id === formState.radio_organization_unit,
    }));

    // @todo: value cannot be a translated label text
    const workaroundOptions = [NOT_LISTED, NOT_SURE].map((wa) => ({
      label: wa.name,
      value: wa.id,
      checked: formState.radio_organization_unit === wa.id,
    }));

    const choices = {
      isUniqueOptions: [
        {
          label: t("pages.claimsDepartment.choiceYes"),
          value: departmentOptions[0]?.value,
          checked:
            formState.radio_organization_unit === departmentOptions[0]?.value,
        },
        {
          label: t("pages.claimsDepartment.choiceNo"),
          value: "choiceNo",
          checked: formState.radio_organization_unit === "choiceNo",
        },
      ],
      departmentOptions: [...departmentOptions, ...workaroundOptions],
      employerDepartmentOptions: [
        ...employerDepartmentOptions,
        ...workaroundOptions,
      ],
    };
    return choices;
  };

  useEffect(() => {
    // lazy loads both departments lists into state
    populateDepartments();
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!departments.length) return () => null;
    // sets radio options to the first workaround option
    // when the claim organization_unit_id is not one of the radio options shown
    // and is instead selected in the combo box component
    const selectedChoice = departmentOptions.find(
      (c) => c.value === initialFormState.organization_unit_id
    );
    const newInitialState = {
      ...initialFormState,
      organization_unit: selectedChoice?.label,
      radio_organization_unit:
        departmentOptions.length && initialFormState.organization_unit_id
          ? typeof selectedChoice !== "undefined"
            ? selectedChoice.value
            : isUnique
            ? "choiceNo"
            : NOT_LISTED.id
          : null,
    };
    updateFields(newInitialState);
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [departments]);

  if (!showDepartments) {
    // @todo: go to next page and ignore departments, auto-select "I'm not sure"
    appLogic.portalFlow.goToNextPage({}, query);
    // return null;
  }

  const { isLong, isShort, isUnique } = getDepartmentListSizes(departments);
  const { isUniqueOptions, departmentOptions, employerDepartmentOptions } =
    getDepartmentOptions();

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <ConditionalContent visible={isUnique}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_organization_unit")}
          choices={isUniqueOptions}
          label={t("pages.claimsDepartment.confirmSectionLabel")}
          hint={
            <React.Fragment>
              <Trans
                i18nKey="pages.claimsDepartment.confirmHint"
                tOptions={{
                  department: departments[0]?.name,
                }}
              />
            </React.Fragment>
          }
          type="radio"
        />
      </ConditionalContent>

      <ConditionalContent visible={isShort}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_organization_unit", {
            fallbackValue: formState.radio_organization_unit || NO.id,
          })}
          choices={departmentOptions}
          label={t("pages.claimsDepartment.sectionLabel")}
          type="radio"
        />
      </ConditionalContent>

      <ConditionalContent
        visible={isLong || hasSelectedRadioWorkaround}
        fieldNamesClearedWhenHidden={["organization_unit"]}
        updateFields={updateFields}
        clearField={clearField}
        getField={getField}
      >
        <Fieldset>
          <ConditionalContent visible={isLong}>
            <FormLabel component="legend">
              {t("pages.claimsDepartment.sectionLabel")}
            </FormLabel>
          </ConditionalContent>
          <ConditionalContent visible={showDepartments}>
            <ComboBox
              {...getFunctionalInputProps("organization_unit", {
                fallbackValue: formState.organization_unit || NOT_LISTED.name,
              })}
              choices={
                hasSelectedRadioWorkaround
                  ? employerDepartmentOptions
                  : departmentOptions
              }
              label={t("pages.claimsDepartment.comboBoxLabel")}
              smallLabel
              required={true}
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

export default withBenefitsApplication(Department);
