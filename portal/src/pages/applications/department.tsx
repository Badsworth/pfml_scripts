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

  // Organization Units
  const EEOrgUnits = claim.employee_organization_units;
  const EROrgUnits = claim.employer_organization_units;
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

  const isSingular = EEOrgUnits.length === 1;
  const isShort = !isSingular && EEOrgUnits.length > 1 && EEOrgUnits.length < 3;
  const isLong = !isSingular && !isShort;

  // Compute default form state
  const { formState, updateFields, getField, clearField } = useFormState(() => {
    const { organization_unit_selection, organization_unit_id } =
      initialFormState || {};
    const radio_org_unit = !isLong
      ? organization_unit_selection || organization_unit_id
      : null;
    const hasRadioWorkaround = !![NOT_LISTED, NOT_SURE, NO].find(
      (w) => w.organization_unit_id === radio_org_unit
    );
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

  // Constructs radio and comboBox available organization_unit options
  const orgUnitAsOption = (dep: OrganizationUnit) => ({
    label: dep.name,
    value: dep.organization_unit_id,
    checked: dep.organization_unit_id === formState.radio_org_unit,
  });

  // Builds the radio/comboBox options for all the different page views
  const getOrgUnitOptions = () => {
    const workaroundOptions = [NOT_LISTED, NOT_SURE].map(orgUnitAsOption);

    const choices = {
      singleOrgUnitOptions: [YES, NO].map(orgUnitAsOption),
      employeeOrgUnitOptions: [
        ...EEOrgUnits.map(orgUnitAsOption),
        ...workaroundOptions,
      ],
      employerOrgUnitOptions: [
        ...EROrgUnits.map(orgUnitAsOption),
        ...workaroundOptions,
      ],
      extraOrgUnitOptions: [
        ...EROrgUnits.filter((o) => !EEOrgUnits.includes(o)).map(
          orgUnitAsOption
        ),
        ...workaroundOptions,
      ],
    };
    return choices;
  };

  const {
    singleOrgUnitOptions,
    extraOrgUnitOptions,
    employeeOrgUnitOptions,
    employerOrgUnitOptions,
  } = getOrgUnitOptions();

  // Determine whether user selected a "workaround" type option
  // while choosing from radio options
  const hasSelectedRadioWorkaround = !![NOT_LISTED, NOT_SURE, NO].find(
    (w) => w.organization_unit_id === formState.radio_org_unit
  );
  // or while choosing from comboBox options
  const hasSelectedComboboxWorkaround = !![NOT_LISTED, NOT_SURE].find(
    (w) => w.organization_unit_id === formState.combobox_org_unit
  );

  // API calls
  const handleSave = async () => {
    const { combobox_org_unit: comboBoxVal, radio_org_unit: radioVal } =
      formState;

    // Auto-selects "I'm not sure"
    // when user doesn't interact with form fields
    if (isLong && comboBoxVal === null) {
      updateFields({
        radio_org_unit: null,
        combobox_org_unit: NOT_SURE.organization_unit_id,
      });
      return;
    }
    if (!isLong && radioVal === null) {
      updateFields({
        radio_org_unit: NOT_SURE.organization_unit_id,
        combobox_org_unit: NOT_SURE.organization_unit_id,
      });
      return;
    }

    const comboBoxId = !hasSelectedComboboxWorkaround ? comboBoxVal : null;
    const radioId = !hasSelectedRadioWorkaround ? radioVal : comboBoxId;
    const comboBoxSel = hasSelectedComboboxWorkaround ? comboBoxVal : null;
    const radioSel = hasSelectedRadioWorkaround ? radioVal : comboBoxSel;

    await appLogic.benefitsApplications.update(claim.application_id, {
      organization_unit_id: isLong ? comboBoxId : radioId,
      organization_unit_selection: isLong ? comboBoxSel : radioSel,
    });
  };

  // Prevents showing the combobox when the only options are workarounds
  const comboBoxHasOnlyWorkarounds =
    hasSelectedRadioWorkaround && extraOrgUnitOptions.length <= 2;

  // The claimant flow should already check both requirements below
  // but we still want to prevent direct access to this page
  if (!showDepartments || EROrgUnits.length === 0) {
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
          <ConditionalContent visible={!comboBoxHasOnlyWorkarounds}>
            <Dropdown
              {...getFunctionalInputProps("combobox_org_unit")}
              choices={
                hasSelectedRadioWorkaround
                  ? extraOrgUnitOptions
                  : employerOrgUnitOptions
              }
              autocomplete={true}
              label={t("pages.claimsOrganizationUnit.comboBoxLabel")}
              smallLabel
            />
          </ConditionalContent>
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
