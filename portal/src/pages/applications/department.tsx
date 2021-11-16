import React, { useEffect, useState } from "react";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import Alert from "../../components/core/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Dropdown from "../../components/core/Dropdown";
import { EmployeeSearchRequest } from "../../api/EmployeesApi";
import Fieldset from "../../components/core/Fieldset";
import FormLabel from "../../components/core/FormLabel";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import { NullableQueryParams } from "../../utils/routeWithParams";
import { OrganizationUnit } from "../../models/Employee";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = [
  "claim.organization_unit_id",
  "claim.organization_unit_selection",
];

interface DepartmentProps extends WithBenefitsApplicationProps {
  query: NullableQueryParams;
}

export const Department = (props: DepartmentProps) => {
  const { appLogic, claim, query } = props;
  const { t } = useTranslation();

  const initialFormState = pick(props, fields).claim;
  const { formState, updateFields, getField, clearField } =
    useFormState(initialFormState);

  // @todo: claim employer org units + appLogic.employees.employee
  const { employee } = appLogic.employees;
  const EEOrgUnits = employee?.organization_units || [];
  const EROrgUnits = claim.employer_organization_units;
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [orgUnits, setOrgUnits] = useState<OrganizationUnit[]>([
    ...EEOrgUnits,
    ...EROrgUnits,
  ]);

  const YES: OrganizationUnit = {
    organization_unit_id: EEOrgUnits[0]?.organization_unit_id,
    name: t("pages.claimsOrganizationUnit.choiceYes"),
  };

  const NO: OrganizationUnit = {
    organization_unit_id: "no",
    name: t("pages.claimsOrganizationUnit.choiceNo"),
  };

  const NOT_LISTED: OrganizationUnit = {
    organization_unit_id: "not_listed",
    name: t("pages.claimsOrganizationUnit.choiceNotListed"),
  };

  const NOT_SURE: OrganizationUnit = {
    organization_unit_id: "not_sure",
    name: t("pages.claimsOrganizationUnit.choiceNotSure"),
  };

  // Determine whether user selected a "workaround" type option
  // while choosing from radio options
  const hasSelectedRadioWorkaround = !![NOT_LISTED, NOT_SURE, NO].find(
    (workaround) => workaround.organization_unit_id === formState.radio_org_unit
  );
  // or while choosing from comboBox options
  const hasSelectedComboboxWorkaround = !![NOT_LISTED, NOT_SURE].find(
    (workaround) =>
      workaround.organization_unit_id === formState.combobox_org_unit
  );

  const skipDepartments = () => {
    appLogic.portalFlow.goToPageFor("CONTINUE", { claim }, query, {
      redirect: true,
    });
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // API calls
  const handleSave = () =>
    // @todo: verify errors come from api validate everything
    appLogic.benefitsApplications.update(claim.application_id, {
      organization_unit_id: formState.combobox_org_unit,
      organization_unit_selection: formState.radio_org_unit,
    });

  const populateOrganizationUnits = async () => {
    // Finds this employee based on name, SSN and employer FEIN and retrieves
    // the employee info alongside the connected organization units
    if (!employee) {
      await appLogic.employees.search({
        first_name: claim.first_name ?? "",
        last_name: claim.last_name ?? "",
        middle_name: claim.middle_name ?? "",
        tax_identifier_last4: claim.tax_identifier?.slice(-4) ?? "",
      } as EmployeeSearchRequest);
    }
    // @todo: verify that "employee" variable is updated after search
    if (
      employee === null ||
      typeof employee.organization_units === "undefined" ||
      !employee.organization_units.length
    ) {
      skipDepartments();
    }
    // @todo check if set state is necessary
    // setOrgUnits([...EEOrgUnits, ...EROrgUnits])
  };

  // Helpers
  const getOrgUnitListSizes = () => {
    const isSingular = EEOrgUnits.length === 1;
    const isShort = !isSingular && EEOrgUnits.length < 6;
    const isLong = !isSingular && !isShort;
    return {
      isLong,
      isShort,
      isSingular,
    };
  };

  const getOrgUnitOptions = () => {
    // Construct radio and comboBox available organization_unit options
    const orgUnitAsOption = (dep: OrganizationUnit) => ({
      label: dep.name,
      value: dep.organization_unit_id,
      checked: dep.organization_unit_id === formState.radio_org_unit,
    });

    const workaroundOptions = [NOT_LISTED, NOT_SURE].map(orgUnitAsOption);

    const choices = {
      singleOrgUnitOptions: [YES, NO].map(orgUnitAsOption),
      allOrgUnitOptions: [
        ...orgUnits.map(orgUnitAsOption),
        ...workaroundOptions,
      ],
      employeeOrgUnitOptions: [
        ...EEOrgUnits.map(orgUnitAsOption),
        ...workaroundOptions,
      ],
      employerOrgUnitOptions: [
        ...EROrgUnits.map(orgUnitAsOption),
        ...workaroundOptions,
      ],
    };
    return choices;
  };

  useEffect(() => {
    // Searches for employee's organization units
    populateOrganizationUnits();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!orgUnits.length) return;

    // @todo: Determine radio / combobox default values based on claim data
    const newInitialState = {
      ...initialFormState,
      combobox_org_unit: null,
      radio_org_unit: null,
    };
    updateFields(newInitialState);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgUnits]);

  const { isLong, isShort, isSingular } = getOrgUnitListSizes();
  const {
    singleOrgUnitOptions,
    allOrgUnitOptions,
    employeeOrgUnitOptions,
    employerOrgUnitOptions,
  } = getOrgUnitOptions();

  if (!orgUnits.length) {
    return null;
  }

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <ConditionalContent visible={isSingular}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_org_unit")}
          choices={singleOrgUnitOptions}
          label={t("pages.claimsOrganizationUnit.confirmSectionLabel")}
          hint={
            <React.Fragment>
              <Trans
                i18nKey="pages.claimsOrganizationUnit.confirmHint"
                tOptions={{
                  organization_unit: employeeOrgUnitOptions[0].label,
                }}
              />
            </React.Fragment>
          }
          type="radio"
        />
      </ConditionalContent>

      <ConditionalContent visible={isShort}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_org_unit")}
          choices={employeeOrgUnitOptions}
          label={t("pages.claimsOrganizationUnit.sectionLabel")}
          type="radio"
        />
      </ConditionalContent>

      <ConditionalContent
        visible={isLong || hasSelectedRadioWorkaround}
        fieldNamesClearedWhenHidden={["combobox_org_unit"]}
        updateFields={updateFields}
        clearField={clearField}
        getField={getField}
      >
        <Fieldset>
          <ConditionalContent visible={isLong}>
            <FormLabel component="legend">
              {t("pages.claimsOrganizationUnit.sectionLabel")}
            </FormLabel>
          </ConditionalContent>
          <Dropdown
            {...getFunctionalInputProps("combobox_org_unit")}
            choices={
              hasSelectedRadioWorkaround
                ? employerOrgUnitOptions
                : allOrgUnitOptions
            }
            autocomplete={true}
            label={t("pages.claimsOrganizationUnit.comboBoxLabel")}
            smallLabel
          />
          <ConditionalContent visible={hasSelectedComboboxWorkaround}>
            <Alert className="measure-6" state="info" slim>
              {t("pages.claimsOrganizationUnit.followupInfo")}
            </Alert>
          </ConditionalContent>
        </Fieldset>
      </ConditionalContent>
    </QuestionPage>
  );
};

export default withBenefitsApplication(Department);
