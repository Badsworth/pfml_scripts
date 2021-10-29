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

  const workarounds: CommonDepartment[] = [
    {
      id: "choiceNotListed",
      name: t("pages.claimsDepartment.choiceNotListed"),
      type: "WORKAROUND",
    },
    {
      id: "choiceNotSure",
      name: t("pages.claimsDepartment.choiceNotSure"),
      type: "WORKAROUND",
    },
  ];

  const hasSelectedRadioWorkaround = !![
    ...workarounds,
    {
      id: "choiceNo",
      name: t("pages.claimsDepartment.choiceNo"),
      type: "WORKAROUND",
    },
  ].find((wa) => wa.id === formState.radio_organization_unit);

  const hasSelectedComboboxWorkaround = !!workarounds.find(
    (wa) => wa.name === formState.organization_unit
  );

  // API calls
  const handleSave = async () => {
    // If user selects a workaround, then take the combobox's value
    // otherwise, take the radio group's value
    const errors = [];

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

    formState.organization_unit_id = employerDepartmentChoices.find(
      (d) =>
        d.label === finalDepartmentDecision ||
        d.value === finalDepartmentDecision
    )?.value;
    delete formState.radio_organization_unit;
    delete formState.organization_unit;
    // console.log("SUBMIT", claim.application_id, formState);
    await appLogic.benefitsApplications.update(claim.application_id, formState);
  };

  const parseDepartments = (
    units: Array<DuaReportingUnit | OrganizationUnit>
  ): CommonDepartment[] => {
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

  const getDepartmentChoices = () => {
    const departmentChoices = departments.map((dep) => ({
      label: dep.name,
      value: dep.id,
      checked: dep.id === formState.radio_organization_unit,
    }));

    const employerDepartmentChoices = employerDepartments.map((dep) => ({
      label: dep.name,
      value: dep.id,
      checked: dep.id === formState.radio_organization_unit,
    }));

    // @todo: value cannot be a translated label text
    const workaroundChoices = workarounds.map((wa) => ({
      label: wa.name,
      value: wa.id,
      checked: formState.radio_organization_unit === wa.id,
    }));

    const choices = {
      isUniqueChoices: [
        {
          label: t("pages.claimsDepartment.choiceYes"),
          value: departmentChoices[0]?.value,
          checked:
            formState.radio_organization_unit === departmentChoices[0]?.value,
        },
        {
          label: t("pages.claimsDepartment.choiceNo"),
          value: "choiceNo",
          checked: formState.radio_organization_unit === "choiceNo",
        },
      ],
      departmentChoices: [...departmentChoices, ...workaroundChoices],
      employerDepartmentChoices: [
        ...employerDepartmentChoices,
        ...workaroundChoices,
      ],
    };
    // console.log(choices);
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
    const selectedChoice = departmentChoices.find(
      (c) => c.value === initialFormState.organization_unit_id
    );
    const newInitialState = {
      ...initialFormState,
      organization_unit: selectedChoice?.label,
      radio_organization_unit:
        departmentChoices.length && initialFormState.organization_unit_id
          ? typeof selectedChoice !== "undefined"
            ? selectedChoice.value
            : isUnique
            ? "choiceNo"
            : workarounds[0].id
          : null,
    };
    updateFields(newInitialState);
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [departments]);

  if (!showDepartments) {
    // @todo: go to next page and ignore departments, auto-select "I'm not sure"
    appLogic.portalFlow.goToNextPage({}, query);
    return null;
  }

  const { isLong, isShort, isUnique } = getDepartmentListSizes(departments);
  const { isUniqueChoices, departmentChoices, employerDepartmentChoices } =
    getDepartmentChoices();

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <ConditionalContent visible={isUnique}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_organization_unit")}
          choices={isUniqueChoices}
          label={t("pages.claimsDepartment.confirmSectionLabel")}
          hint={
            <React.Fragment>
              <Trans
                i18nKey="pages.claimsDepartment.confirmHint"
                tOptions={{
                  department: departments[0]?.name,
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
          {...getFunctionalInputProps("radio_organization_unit", {
            fallbackValue: formState.radio_organization_unit || "",
          })}
          choices={departmentChoices}
          label={t("pages.claimsDepartment.sectionLabel")}
          // hint={t("pages.claimsDepartment.hint")}
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
            <FormLabel
              component="legend"
              // hint={t("pages.claimsDepartment.hint")}
            >
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
                  ? employerDepartmentChoices
                  : departmentChoices
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
