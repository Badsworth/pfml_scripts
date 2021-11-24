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

export const Department = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const showDepartments = isFeatureEnabled("claimantShowOrganizationUnits");

  const initialFormState = pick(props, fields).claim;

  // Organization Units (see class BenefitsApplication)
  const EEOrgUnits = claim.employee_organization_units ?? [];
  const extraOrgUnits = claim.extraEROrgUnits;

  // Below are radio/combobox options that are not real organization units,
  // which will be referred to as "workarounds", but are still available to the user
  // We're defining them with the "OrganizationUnit" type to simplify
  // creating or modifying our lists of options used in the radio & combobox
  const YES: OrganizationUnit = {
    organization_unit_id: EEOrgUnits[0]?.organization_unit_id,
    name: t("pages.claimsOrganizationUnit.choiceYes"),
  };
  const NOT_LISTED: OrganizationUnit = {
    organization_unit_id: "not_listed",
    name: t("pages.claimsOrganizationUnit.choiceNotListed"),
  };
  const NOT_SURE: OrganizationUnit = {
    organization_unit_id: "not_selected",
    name: t("pages.claimsOrganizationUnit.choiceNotSure"),
  };
  const NO: OrganizationUnit = {
    ...NOT_SURE,
    name: t("pages.claimsOrganizationUnit.choiceNo"),
  };

  // The length of the employee's org units is what determines
  // which "view" to show to the user
  const isSingular = EEOrgUnits.length === 1;
  const isShort = !isSingular && EEOrgUnits.length > 1 && EEOrgUnits.length < 3;
  const isLong = !isSingular && !isShort;

  // Compute default form state
  const { formState, updateFields, getField, clearField } = useFormState(() => {
    // Initial state coming from the API
    const {
      // "selection" will be "not_listed", "not_selected" or null
      organization_unit_selection,
      // "id" will be uuid or null
      organization_unit_id,
    } = initialFormState || {};

    // The value of the radio form field is determined,
    // defaulting to the "organization_unit_selection" value
    // and if there is no "selection", the "organization_unit_id"
    // When we're in the "isLong" list view, its null
    const radio_org_unit = !isLong
      ? organization_unit_selection || organization_unit_id
      : null;

    // Determine whether the selected radio option is a "workaround"
    const hasRadioWorkaround = !![NOT_LISTED, NOT_SURE, NO].find(
      (w) => w.organization_unit_id === radio_org_unit
    );

    // The value of the combobox form field is determined
    // and usually it will be directly "organization_unit_id"
    // except if the "id" is null or we're in a view with radio options
    // and a "workaround" was not selected, then we default to the "selection"
    const combobox_org_unit =
      (!isLong
        ? hasRadioWorkaround
          ? organization_unit_id
          : null
        : organization_unit_id) || organization_unit_selection;
    return {
      combobox_org_unit,
      radio_org_unit,
    };
  });

  // Form fields' props
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // Converts an OrganizationUnit into a form field's option
  const orgUnitAsOption = (dep: OrganizationUnit) => ({
    label: dep.name,
    value: dep.organization_unit_id,
    checked: dep.organization_unit_id === formState.radio_org_unit,
  });

  // Builds the radio/comboBox options for all the different page views
  const workaroundOptions = [NOT_LISTED, NOT_SURE].map(orgUnitAsOption);

  // First page view with Yes, No radio options
  const singleOrgUnitOptions = [YES, NO].map(orgUnitAsOption);
  // Second page view with multiple, but few radio options
  const employeeOrgUnitOptions = EEOrgUnits.map(orgUnitAsOption);
  // Third page view all possible options in a combobox
  // After the user selects a "workaround" radio option
  // and combobox shows up, these are the remaining options
  // takes all possible options and filters out the ones shown in radio options
  const extraOrgUnitOptions = extraOrgUnits.map(orgUnitAsOption);

  // Determine whether user selected a "workaround" option
  // while choosing from radio options
  const hasSelectedRadioWorkaround = !![NOT_LISTED, NOT_SURE, NO].find(
    (w) => w.organization_unit_id === formState.radio_org_unit
  );
  // Determine whether user selected a "workaround" option
  // while choosing from combobox options
  const hasSelectedComboboxWorkaround = !![NOT_LISTED, NOT_SURE].find(
    (w) => w.organization_unit_id === formState.combobox_org_unit
  );

  // API calls
  const handleSave = async () => {
    const { combobox_org_unit: comboBoxVal, radio_org_unit: radioVal } =
      formState;

    // @todo: add api validation when both fields are null

    // Splits "workaround" or the "selection" values from real UUID values
    const comboBoxId = !hasSelectedComboboxWorkaround ? comboBoxVal : null;
    const radioId = !hasSelectedRadioWorkaround ? radioVal : comboBoxId;
    const comboBoxSel = hasSelectedComboboxWorkaround ? comboBoxVal : null;
    const radioSel = hasSelectedRadioWorkaround ? radioVal : comboBoxSel;

    await appLogic.benefitsApplications.update(claim.application_id, {
      // Based on the current page view, determine which form field value to use per field
      organization_unit_id: isLong ? comboBoxId : radioId,
      organization_unit_selection: isLong ? comboBoxSel : radioSel,
    });
  };

  // Prevents showing the combobox when the only options are "workarounds"
  // Will only happen both the employer and employee organization unit lists
  // are equal and small
  const comboBoxHasOnlyWorkarounds =
    hasSelectedRadioWorkaround && extraOrgUnitOptions.length === 0;

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
      {/* Show this page view if there is only one employee organization unit */}
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

      {/* Show this page view if there is two to five employee organization units */}
      <ConditionalContent visible={isShort}>
        <InputChoiceGroup
          {...getFunctionalInputProps("radio_org_unit")}
          choices={employeeOrgUnitOptions.concat(workaroundOptions)}
          label={t("pages.claimsOrganizationUnit.sectionLabel")}
          type="radio"
        />
      </ConditionalContent>

      {/* Show this page view if there is more than five employee organization units
          or the user selected a "workaround" option in the radio form fields above */}
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
          {/* Only show this combobox if there's more organization units
              to choose from other than the ones already on screen */}
          <ConditionalContent visible={!comboBoxHasOnlyWorkarounds}>
            <Dropdown
              {...getFunctionalInputProps("combobox_org_unit")}
              choices={extraOrgUnitOptions
                .concat(
                  hasSelectedRadioWorkaround ? employeeOrgUnitOptions : []
                )
                .concat(workaroundOptions)}
              autocomplete={true}
              label={t("pages.claimsOrganizationUnit.comboBoxLabel")}
              smallLabel
            />
          </ConditionalContent>

          {/* When user selects a combobox "workaround" option 
              or the combobox is empty, show an info alert */}
          <ConditionalContent
            visible={
              hasSelectedComboboxWorkaround || comboBoxHasOnlyWorkarounds
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
