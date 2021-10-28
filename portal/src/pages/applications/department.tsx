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
  console.log(initialFormState);
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

  const hasSelectedRadioWorkaround = [
    ...workarounds,
    {
      id: "choiceNo",
      name: t("pages.claimsDepartment.choiceNo"),
      type: "WORKAROUND",
    },
  ].includes(formState.radio_organization_unit);
  const hasSelectedComboboxWorkaround = workarounds.includes(
    formState.organization_unit_id
  );

  // API calls
  const handleSave = async () => {
    // If user selects a workaround, then take the combobox's value
    // otherwise, take the radio group's value
    const errors = [];

    const finalDepartmentDecision =
      hasSelectedRadioWorkaround || isLong
        ? formState.organization_unit_id
        : formState.radio_organization_unit;

    formState.organization_unit_id = finalDepartmentDecision;

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
      (isLong && !formState.organization_unit_id) ||
      (!isLong &&
        formState.radio_organization_unit &&
        !formState.organization_unit_id)
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

    delete formState.radio_organization_unit;
    formState.organization_unit_id = finalDepartmentDecision;
    console.log(claim.application_id, formState);
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
        console.log({ employerDeps });
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

  const getDepartmentChoices = (deps: CommonDepartment[]) => {
    if (!deps.length) return [];

    const departmentChoices = deps.map((dep) => ({
      label: dep.name,
      value: dep.id,
      checked: dep.name === formState.radio_organization_unit,
    }));

    // @todo: value cannot be a translated label text
    const workaroundChoices = workarounds.map((wa) => ({
      label: wa.name,
      value: wa.id,
      checked: formState.radio_organization_unit === wa.id,
    }));
    if (deps.length === 1) {
      return [
        {
          label: t("pages.claimsDepartment.choiceYes"),
          value: deps[0].id,
          checked: formState.radio_organization_unit === deps[0].id,
        },
        {
          label: t("pages.claimsDepartment.choiceNo"),
          value: "choiceNo",
          checked: formState.radio_organization_unit === "choiceNo",
        },
      ];
    } else {
      return [...departmentChoices, ...workaroundChoices];
    }
  };

  useEffect(() => {
    // lazy loads both departments lists into state
    populateDepartments();
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (isLong || !departments.length) return () => null;
    // sets radio options to the first workaround option
    // when the claim organization_unit_id is not one of the radio options shown
    // and is instead selected in the combo box component
    updateFields({
      ...initialFormState,
      radio_organization_unit:
        claimantChoices.length && initialFormState.organization_unit_id
          ? claimantChoices.find(
              (c) => c.value === initialFormState.organization_unit_id
            )
            ? initialFormState.organization_unit_id
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
    appLogic.portalFlow.goToNextPage({}, query);
    return null;
  }

  const { isLong, isShort, isUnique } = getDepartmentListSizes(departments);
  const claimantChoices = getDepartmentChoices(departments);
  const employerChoices = getDepartmentChoices(employerDepartments);
  console.log({
    claimantChoices,
    employerChoices,
  });
  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <ConditionalContent visible={isUnique}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_organization_unit")}
          choices={claimantChoices}
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
          choices={claimantChoices}
          label={t("pages.claimsDepartment.sectionLabel")}
          // hint={t("pages.claimsDepartment.hint")}
          type="radio"
        />
      </ConditionalContent>

      <ConditionalContent
        visible={isLong || hasSelectedRadioWorkaround}
        fieldNamesClearedWhenHidden={["organization_unit_id"]}
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
                fallbackValue: formState.organization_unit_id || "",
              })}
              choices={
                hasSelectedRadioWorkaround ? employerChoices : claimantChoices
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
