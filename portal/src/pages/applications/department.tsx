import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import Alert from "../../components/core/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Dropdown from "../../components/core/Dropdown";
import Fieldset from "../../components/core/Fieldset";
import FormLabel from "../../components/core/FormLabel";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import OrganizationUnit from "../../models/OrganizationUnit";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = [
  "claim.organization_unit_id",
  "claim.organization_unit_selection",
];

type RadioOrComboboxField = "comboOrgUnit" | "radioOrgUnit";

export const Department = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const showDepartments = isFeatureEnabled("claimantShowOrganizationUnits");

  const { organization_unit_id, organization_unit_selection } = pick(
    props,
    fields
  ).claim || {
    organization_unit_id: null,
    organization_unit_selection: null,
  };

  // Determine which view to use by the total count of employee org units
  // DUA = Division of Unemployment Assistance
  const DUAOrgUnitCount = claim.employee_organization_units.length;
  const isConfirmationView = DUAOrgUnitCount === 1;
  const isDropdownView = !isConfirmationView;

  const firstDUAOrgUnitId =
    claim.employee_organization_units[0]?.organization_unit_id;

  const defaultRadioVal =
    organization_unit_id && organization_unit_id !== firstDUAOrgUnitId
      ? "no"
      : organization_unit_id;

  const defaultComboboxVal =
    organization_unit_id || organization_unit_selection;

  const { formState, updateFields, getField, clearField } = useFormState({
    comboOrgUnit: defaultComboboxVal,
    radioOrgUnit: defaultRadioVal || "",
  });

  // Form fields' props
  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const workarounds = ["not_selected", "no"];
  // Determine whether user selected a "workaround" option in a field's options
  const hasSelectedWorkaroundFor = (field: RadioOrComboboxField) =>
    workarounds.includes(formState[field]);

  const imNotSureOption = {
    label: t("pages.claimsOrganizationUnit.choiceNotSure"),
    value: "not_selected",
    checked: formState.comboOrgUnit === "not_selected",
  };

  // Radio options for confirmation view
  const confirmationOptions = [
    {
      label: t("pages.claimsOrganizationUnit.choiceYes"),
      value: firstDUAOrgUnitId,
      checked: formState.radioOrgUnit === firstDUAOrgUnitId,
    },
    {
      label: t("pages.claimsOrganizationUnit.choiceNo"),
      value: "no",
      checked:
        formState.radioOrgUnit && formState.radioOrgUnit !== firstDUAOrgUnitId,
    },
  ];

  // All combobox options in the order: employee units, employer units, workarounds
  // Options shown will vary depending on current page view
  const comboBoxOptions = (
    isDropdownView ? claim.employee_organization_units : []
  )
    .concat(claim.extraOrgUnits)
    .map((dep: OrganizationUnit) => ({
      label: dep.name,
      value: dep.organization_unit_id,
      checked: dep.organization_unit_id === formState.comboOrgUnit,
    }))
    .concat(imNotSureOption);

  const comboBoxHasOnlyWorkarounds = comboBoxOptions.length === 1;
  // API calls
  const handleSave = async () => {
    const { radioOrgUnit, comboOrgUnit } = formState;

    // Populate organization_unit_id with the selected organization unit uuid, if any.
    const comboBoxId = !hasSelectedWorkaroundFor("comboOrgUnit")
      ? comboOrgUnit
      : null;
    const radioId = !hasSelectedWorkaroundFor("radioOrgUnit")
      ? radioOrgUnit
      : comboBoxId;
    // Populate organization_unit_selection with the selected workaround value, if any.
    const comboBoxSel = hasSelectedWorkaroundFor("comboOrgUnit")
      ? comboOrgUnit
      : null;

    await appLogic.benefitsApplications.update(claim.application_id, {
      // Based on the current page view, determine which form field value to use per field
      organization_unit_id: isDropdownView ? comboBoxId : radioId,
      organization_unit_selection: comboBoxSel,
    });
  };

  // The claimant flow should already check both requirements below
  // but we still want to prevent direct access to this page
  // if the feature flag is False or this employer has zero org units
  if (!showDepartments || claim.employer_organization_units.length === 0) {
    appLogic.portalFlow.goToNextPage(
      { claim },
      { claim_id: claim.application_id }
    );
    return null;
  }

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <ConditionalContent visible={isConfirmationView}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radioOrgUnit")}
          choices={confirmationOptions}
          label={t("pages.claimsOrganizationUnit.confirmSectionLabel")}
          hint={
            <Trans
              i18nKey="pages.claimsOrganizationUnit.confirmHint"
              tOptions={{
                organization_unit: claim.employee_organization_units[0]?.name,
              }}
            />
          }
          type="radio"
        />
      </ConditionalContent>
      <ConditionalContent
        visible={isDropdownView || hasSelectedWorkaroundFor("radioOrgUnit")}
        fieldNamesClearedWhenHidden={["comboOrgUnit"]}
        updateFields={updateFields}
        clearField={clearField}
        getField={getField}
      >
        <Fieldset>
          <ConditionalContent visible={isDropdownView}>
            <FormLabel component="legend">
              {t("pages.claimsOrganizationUnit.sectionLabel")}
            </FormLabel>
          </ConditionalContent>
          <ConditionalContent visible={!comboBoxHasOnlyWorkarounds}>
            <p>{t("pages.claimsOrganizationUnit.failureWarning")}</p>
            <Dropdown
              {...getFunctionalInputProps("comboOrgUnit")}
              choices={comboBoxOptions}
              autocomplete={true}
              label={t("pages.claimsOrganizationUnit.comboBoxLabel")}
              smallLabel
            />
          </ConditionalContent>
          <ConditionalContent
            visible={
              hasSelectedWorkaroundFor("comboOrgUnit") ||
              comboBoxHasOnlyWorkarounds
            }
          >
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
