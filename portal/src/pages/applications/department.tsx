import React, { useEffect, useState } from "react";

import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Alert from "../../components/core/Alert";
import AppErrorInfo from "../../models/AppErrorInfo";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConditionalContent from "../../components/ConditionalContent";
import Dropdown from "../../components/core/Dropdown";
import { EmployeeOrganizationUnit } from "../../models/Employee";
import { EmployeeSearchRequest } from "../../api/EmployeesApi";
import Fieldset from "../../components/core/Fieldset";
import FormLabel from "../../components/core/FormLabel";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import { NullableQueryParams } from "../../utils/routeWithParams";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.organization_unit_id"];

interface OrganizationUnitProps extends WithBenefitsApplicationProps {
  query: NullableQueryParams;
}

export const OrganizationUnit = (props: OrganizationUnitProps) => {
  const { appLogic, claim, query } = props;
  const { t } = useTranslation();

  const showOrganizationUnits = isFeatureEnabled(
    "claimantShowOrganizationUnits"
  );

  const initialFormState = pick(props, fields).claim;
  const { formState, updateFields, getField, clearField } =
    useFormState(initialFormState);

  const [organizationUnits, setOrganizationUnits] = useState<
    EmployeeOrganizationUnit[]
  >([]);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const NO: EmployeeOrganizationUnit = {
    organization_unit_id: "choiceNo",
    name: t("pages.claimsOrganizationUnit.choiceNo"),
    linked: false,
    fineos_id: null,
    employer_id: null,
  };

  const NOT_LISTED: EmployeeOrganizationUnit = {
    organization_unit_id: "choiceNotListed",
    name: t("pages.claimsOrganizationUnit.choiceNotListed"),
    linked: false,
    fineos_id: null,
    employer_id: null,
  };

  const NOT_SURE: EmployeeOrganizationUnit = {
    organization_unit_id: "choiceNotSure",
    name: t("pages.claimsOrganizationUnit.choiceNotSure"),
    linked: false,
    fineos_id: null,
    employer_id: null,
  };

  // Determine whether user selected a "workaround" type option
  // while choosing from radio options
  const hasSelectedRadioWorkaround = !![NOT_LISTED, NOT_SURE, NO].find(
    (workaround) =>
      workaround.organization_unit_id === formState.radio_organization_unit
  );
  // or while choosing from comboBox options
  const hasSelectedComboboxWorkaround = !![NOT_LISTED, NOT_SURE].find(
    (workaround) =>
      workaround.organization_unit_id === formState.combobox_organization_unit
  );

  const skipDepartments = () => {
    appLogic.portalFlow.goToPageFor("CONTINUE", { claim }, query, {
      redirect: true,
    });
  };

  // API calls
  const handleSave = async () => {
    const errors = [];

    // This field validation is not in the API due to
    // the organization_unit_id being nullable and the API does not have
    // the context to deal with two separate form fields that conditionally
    // become required
    if (isSingular && !formState.radio_organization_unit) {
      errors.push(
        new AppErrorInfo({
          field: "radio_organization_unit",
          message: t("pages.claimsOrganizationUnit.errors.missingConfirmation"),
          type: "required",
        })
      );
    }
    if (
      ((isSingular || isShort) &&
        hasSelectedRadioWorkaround &&
        !formState.combobox_organization_unit) ||
      (isShort && !formState.radio_organization_unit) ||
      (isLong && !formState.combobox_organization_unit)
    ) {
      errors.push(
        new AppErrorInfo({
          field:
            isShort && !formState.radio_organization_unit
              ? "radio_organization_unit"
              : "organization_unit_id",
          message: t(
            "pages.claimsOrganizationUnit.errors.missingOrganizationUnit"
          ),
          type: "required",
        })
      );
    }

    if (errors.length > 0) {
      appLogic.setAppErrors(new AppErrorInfoCollection(errors));
      return;
    }

    const finalOrganizationUnitDecision: string =
      hasSelectedRadioWorkaround || isLong
        ? formState.combobox_organization_unit
        : formState.radio_organization_unit;

    // If user selected a workaround option, then remove org unit from claim
    // falls back into manual process
    const noGoodOption =
      finalOrganizationUnitDecision === NOT_LISTED.organization_unit_id ||
      finalOrganizationUnitDecision === NOT_SURE.organization_unit_id;

    await appLogic.benefitsApplications.update(claim.application_id, {
      organization_unit_id: noGoodOption ? null : finalOrganizationUnitDecision,
    });
  };

  const populateOrganizationUnits = async () => {
    // Finds this employee based on name, SSN and employer FEIN and retrieves
    // the employee info alongside the connected organization units
    if (!organizationUnits.length) {
      const searchEmployee: EmployeeSearchRequest = {
        first_name: claim.first_name ?? "",
        last_name: claim.last_name ?? "",
        middle_name: claim.middle_name ?? "",
        tax_identifier_last4: claim.tax_identifier?.slice(-4) ?? "",
        employer_fein: claim.employer_fein ?? "",
      };
      const employee = await appLogic.employees.search(searchEmployee);
      if (employee) {
        // When the employee search does not return organization units
        // then the employer also does not have any, so go to next page
        if (
          typeof employee.organization_units === "undefined" ||
          employee.organization_units.length === 0
        ) {
          skipDepartments();
        }
        setOrganizationUnits(employee.organization_units || []);
      }
    }
  };

  // Helpers
  const getOrganizationUnitListSizes = () => {
    const linkedOrganizationUnits = organizationUnits.filter(
      (organization_unit) => organization_unit.linked
    );
    const isSingular = linkedOrganizationUnits.length === 1;
    const isShort =
      linkedOrganizationUnits.length > 1 && linkedOrganizationUnits.length <= 3;
    const isLong =
      !isSingular &&
      !isShort &&
      (linkedOrganizationUnits.length > 3 ||
        organizationUnits.length > linkedOrganizationUnits.length);
    return {
      isLong,
      isShort,
      isSingular,
    };
  };

  const getOrganizationUnitOptions = () => {
    // Construct radio and comboBox available organization_unit options
    const organizationUnitAsOption = (dep: EmployeeOrganizationUnit) => ({
      label: dep.name,
      value: dep.organization_unit_id,
      checked: dep.organization_unit_id === formState.radio_organization_unit,
    });

    const workaroundOptions = [NOT_LISTED, NOT_SURE].map((wa) => ({
      label: wa.name,
      value: wa.organization_unit_id,
      checked: formState.radio_organization_unit === wa.organization_unit_id,
    }));
    const linkedOrganizationUnits = organizationUnits.filter(
      (dep) => dep.linked
    );
    const choices = {
      oneOrganizationUnitOptions: [
        {
          label: t("pages.claimsOrganizationUnit.choiceYes"),
          value: linkedOrganizationUnits[0]?.organization_unit_id,
          checked:
            formState.radio_organization_unit ===
            linkedOrganizationUnits[0]?.organization_unit_id,
        },
        {
          label: NO.name,
          value: NO.organization_unit_id,
          checked:
            formState.radio_organization_unit === NO.organization_unit_id,
        },
      ],
      allOrganizationUnitOptions: [
        ...organizationUnits.map(organizationUnitAsOption),
        ...workaroundOptions,
      ],
      linkedOrganizationUnitOptions: [
        ...linkedOrganizationUnits.map(organizationUnitAsOption),
        ...workaroundOptions,
      ],
      unlinkedOrganizationUnitOptions: [
        ...organizationUnits
          .filter((dep) => !dep.linked)
          .map(organizationUnitAsOption),
        ...workaroundOptions,
      ],
    };
    return choices;
  };

  useEffect(() => {
    if (!showOrganizationUnits) {
      skipDepartments();
      return;
    }
    // lazy loads both organizationUnits lists into state
    populateOrganizationUnits();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!organizationUnits.length) return;

    const selectedChoice = organizationUnits.find(
      (c) => c.organization_unit_id === initialFormState?.organization_unit_id
    );

    const hasValidValue = typeof selectedChoice !== "undefined";
    const hasDefaultValue =
      initialFormState?.organization_unit_id !== null &&
      organizationUnits.length > 0;

    // Determines radio / combobox default values based on claim.organization_unit_id
    const newInitialState = {
      ...initialFormState,
      combobox_organization_unit: hasDefaultValue
        ? hasValidValue
          ? isLong || !selectedChoice.linked
            ? selectedChoice.organization_unit_id
            : null
          : null
        : null,
      radio_organization_unit:
        hasDefaultValue && !isLong
          ? hasValidValue
            ? selectedChoice.linked
              ? selectedChoice.organization_unit_id
              : isSingular
              ? NO.organization_unit_id
              : NOT_LISTED.organization_unit_id
            : null
          : null,
    };
    updateFields(newInitialState);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [organizationUnits]);

  const { isLong, isShort, isSingular } = getOrganizationUnitListSizes();
  const {
    oneOrganizationUnitOptions,
    allOrganizationUnitOptions,
    linkedOrganizationUnitOptions,
    unlinkedOrganizationUnitOptions,
  } = getOrganizationUnitOptions();

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <ConditionalContent visible={isSingular}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_organization_unit")}
          choices={oneOrganizationUnitOptions}
          label={t("pages.claimsOrganizationUnit.confirmSectionLabel")}
          hint={
            <React.Fragment>
              <Trans
                i18nKey="pages.claimsOrganizationUnit.confirmHint"
                tOptions={{
                  organization_unit: linkedOrganizationUnitOptions[0].label,
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
          choices={linkedOrganizationUnitOptions}
          label={t("pages.claimsOrganizationUnit.sectionLabel")}
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
              {t("pages.claimsOrganizationUnit.sectionLabel")}
            </FormLabel>
          </ConditionalContent>
          <ConditionalContent visible={showOrganizationUnits}>
            <Dropdown
              {...getFunctionalInputProps("combobox_organization_unit", {
                fallbackValue: formState.combobox_organization_unit || "",
              })}
              choices={
                hasSelectedRadioWorkaround
                  ? unlinkedOrganizationUnitOptions
                  : allOrganizationUnitOptions
              }
              autocomplete={true}
              label={t("pages.claimsOrganizationUnit.comboBoxLabel")}
              smallLabel
            />
          </ConditionalContent>
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

export default withBenefitsApplication(OrganizationUnit);
