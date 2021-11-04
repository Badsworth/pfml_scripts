import React, { useEffect, useState } from "react";

import Alert from "../../components/Alert";
import AppErrorInfo from "../../models/AppErrorInfo";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import { AppLogic } from "../../hooks/useAppLogic";
import BenefitsApplication from "../../models/BenefitsApplication";
import ComboBox from "../../components/ComboBox";
import ConditionalContent from "../../components/ConditionalContent";
import { EmployeeOrganizationUnit } from "../../models/User";
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

export const Department = (props: DepartmentProps) => {
  const { appLogic, claim, query } = props;
  const { t } = useTranslation();

  const showDepartments = isFeatureEnabled("claimantShowDepartments");

  const initialFormState = pick(props, fields).claim;
  const { formState, updateFields, getField, clearField } =
    useFormState(initialFormState);

  const [departments, setDepartments] = useState<EmployeeOrganizationUnit[]>(
    []
  );

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const NO: EmployeeOrganizationUnit = {
    organization_unit_id: "choiceNo",
    name: t("pages.claimsDepartment.choiceNo"),
    linked: false,
  };

  const NOT_LISTED: EmployeeOrganizationUnit = {
    organization_unit_id: "choiceNotListed",
    name: t("pages.claimsDepartment.choiceNotListed"),
    linked: false,
  };

  const NOT_SURE: EmployeeOrganizationUnit = {
    organization_unit_id: "choiceNotSure",
    name: t("pages.claimsDepartment.choiceNotSure"),
    linked: false,
  };

  // Determine whether user selected a "workaround" type option
  // while choosing from radio options
  const hasSelectedRadioWorkaround = !![NOT_LISTED, NOT_SURE, NO].find(
    (wa) => wa.organization_unit_id === formState.radio_organization_unit
  );
  // or while choosing from comboBox options
  const hasSelectedComboboxWorkaround = !![NOT_LISTED, NOT_SURE].find(
    (wa) => wa.name === formState.organization_unit
  );

  // API calls
  const handleSave = async () => {
    const errors = [];

    if (isUnique && !formState.radio_organization_unit) {
      errors.push(
        new AppErrorInfo({
          field: "radio_organization_unit",
          message: t("pages.claimsDepartment.errors.missingConfirmation"),
          type: "required",
        })
      );
    }
    if (
      ((isUnique || isShort) &&
        hasSelectedRadioWorkaround &&
        !formState.organization_unit) ||
      (isShort && !formState.radio_organization_unit) ||
      (isLong && !formState.organization_unit)
    ) {
      errors.push(
        new AppErrorInfo({
          field:
            isShort && !formState.radio_organization_unit
              ? "radio_organization_unit"
              : "organization_unit_id",
          message: t("pages.claimsDepartment.errors.missingDepartment"),
          type: "required",
        })
      );
    }

    appLogic.setAppErrors(new AppErrorInfoCollection(errors));

    if (errors.length > 0) return;
    // If user selects a workaround, then take the combobox's value
    // otherwise, take the radio group's value
    const finalDepartmentDecision =
      hasSelectedRadioWorkaround || isLong
        ? formState.organization_unit
        : formState.radio_organization_unit;

    const selectedDepartment = allDepartmentOptions.find(
      (d) =>
        d.label === finalDepartmentDecision ||
        d.value === finalDepartmentDecision
    );

    if (
      selectedDepartment.value === NOT_LISTED.organization_unit_id ||
      selectedDepartment.value === NOT_SURE.organization_unit_id
    ) {
      selectedDepartment.value = null;
    }

    await appLogic.benefitsApplications.update(claim.application_id, {
      organization_unit_id: selectedDepartment.value,
    });
  };

  const populateDepartments = async () => {
    // Finds this employee based on name, SSN and employer FEIN and retrieves
    // the employee info alongside the connected organization units
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
        setDepartments(employee.organization_units || []);
      }
      // @todo: if employee not found, api should handle the error response
    }
  };

  // Helpers
  const getDepartmentListSizes = () => {
    const linkedDepartments = departments.filter(
      (department) => department.linked
    );
    const isUnique = linkedDepartments.length === 1;
    const isShort =
      linkedDepartments.length > 1 && linkedDepartments.length <= 3;
    const isLong =
      !isUnique &&
      !isShort &&
      (linkedDepartments.length > 3 ||
        departments.length > linkedDepartments.length);
    return {
      isLong,
      isShort,
      isUnique,
    };
  };

  const getDepartmentOptions = () => {
    // Construct radio and comboBox available department options
    const departmentAsOption = (dep: EmployeeOrganizationUnit) => ({
      label: dep.name,
      value: dep.organization_unit_id,
      checked: dep.organization_unit_id === formState.radio_organization_unit,
    });

    const workaroundOptions = [NOT_LISTED, NOT_SURE].map((wa) => ({
      label: wa.name,
      value: wa.organization_unit_id,
      checked: formState.radio_organization_unit === wa.organization_unit_id,
    }));
    const linkedDepartments = departments.filter((dep) => dep.linked);
    const choices = {
      oneDepartmentOptions: [
        {
          label: t("pages.claimsDepartment.choiceYes"),
          value: linkedDepartments[0]?.organization_unit_id,
          checked:
            formState.radio_organization_unit ===
            linkedDepartments[0]?.organization_unit_id,
        },
        {
          label: NO.name,
          value: NO.organization_unit_id,
          checked:
            formState.radio_organization_unit === NO.organization_unit_id,
        },
      ],
      allDepartmentOptions: [
        ...departments.map(departmentAsOption),
        ...workaroundOptions,
      ],
      linkedDepartmentOptions: [
        ...linkedDepartments.map(departmentAsOption),
        ...workaroundOptions,
      ],
      unlinkedDepartmentOptions: [
        ...departments.filter((dep) => !dep.linked).map(departmentAsOption),
        ...workaroundOptions,
      ],
    };
    return choices;
  };

  useEffect(() => {
    if (!showDepartments) {
      appLogic.portalFlow.goToPageFor("CONTINUE", { claim }, query, {
        redirect: true,
      });
      return () => null;
    }
    // lazy loads both departments lists into state
    populateDepartments();
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!departments.length) return () => null;

    const selectedChoice = departments.find(
      (c) => c.organization_unit_id === initialFormState.organization_unit_id
    );

    const hasDefaultValue =
      departments.length && initialFormState.organization_unit_id;
    const hasValidValue = typeof selectedChoice !== "undefined";

    // Determines radio / combobox default values based on claim.organization_unit_id
    const newInitialState = {
      ...initialFormState,
      organization_unit: hasDefaultValue
        ? hasValidValue
          ? isLong || !selectedChoice.linked
            ? selectedChoice.name
            : null
          : NOT_LISTED.name
        : null,
      radio_organization_unit: hasDefaultValue
        ? hasValidValue
          ? selectedChoice.linked
            ? selectedChoice.organization_unit_id
            : isUnique
            ? NO.organization_unit_id
            : NOT_LISTED.organization_unit_id
          : NOT_LISTED.organization_unit_id
        : null,
    };
    updateFields(newInitialState);
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [departments]);

  const { isLong, isShort, isUnique } = getDepartmentListSizes();
  const {
    oneDepartmentOptions,
    allDepartmentOptions,
    linkedDepartmentOptions,
    unlinkedDepartmentOptions,
  } = getDepartmentOptions();

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <ConditionalContent visible={isUnique}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_organization_unit")}
          choices={oneDepartmentOptions}
          label={t("pages.claimsDepartment.confirmSectionLabel")}
          hint={
            <React.Fragment>
              <Trans
                i18nKey="pages.claimsDepartment.confirmHint"
                tOptions={{
                  department: linkedDepartmentOptions[0].label,
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
            fallbackValue: formState.radio_organization_unit || "",
          })}
          choices={linkedDepartmentOptions}
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
                fallbackValue: formState.organization_unit || "",
              })}
              choices={
                hasSelectedRadioWorkaround
                  ? unlinkedDepartmentOptions
                  : allDepartmentOptions
              }
              label={t("pages.claimsDepartment.comboBoxLabel")}
              smallLabel
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
