import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import Alert from "../../components/core/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Dropdown from "../../components/core/Dropdown";
import Fieldset from "../../components/core/Fieldset";
import FormLabel from "../../components/core/FormLabel";
import OrganizationUnit from "../../models/OrganizationUnit";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
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

  const { organization_unit_id, organization_unit_selection } =
    initialFormState || {};

  const { formState, updateFields } = useFormState({
    combobox_org_unit: organization_unit_id || organization_unit_selection,
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
    checked: dep.organization_unit_id === formState.combobox_org_unit,
  });

  // Below are combobox options that are not real organization units,
  // but are still available to the user, which will be referred to as "workarounds"
  const workarounds = ["not_listed", "not_selected"];
  const workaroundOptions = [
    {
      label: t("pages.claimsOrganizationUnit.choiceNotListed"),
      value: "not_listed",
      checked: formState.combo_org_unit === "not_listed",
    },
    {
      label: t("pages.claimsOrganizationUnit.choiceNotSure"),
      value: "not_selected",
      checked: formState.combo_org_unit === "not_selected",
    },
  ];

  // All combobox options in the order: employee units, employer units, workarounds
  const comboBoxOptions = claim.employee_organization_units
    .concat(claim.extraOrgUnits)
    .map(orgUnitAsOption)
    .concat(workaroundOptions);

  // Determine whether user selected a "workaround" option in the combobox
  const hasSelectedComboboxWorkaround = workarounds.includes(
    formState.combobox_org_unit
  );

  // API calls
  const handleSave = async () => {
    const { combobox_org_unit } = formState;

    await appLogic.benefitsApplications.update(claim.application_id, {
      // Parse the data based on hasSelectedComboboxWorkaround
      organization_unit_id: !hasSelectedComboboxWorkaround
        ? combobox_org_unit
        : null,
      organization_unit_selection: hasSelectedComboboxWorkaround
        ? combobox_org_unit
        : null,
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
      <Fieldset>
        <FormLabel component="legend">
          {t("pages.claimsOrganizationUnit.sectionLabel")}
        </FormLabel>
        {/* Only show this combobox if there's organization units to choose from */}
        <Dropdown
          {...getFunctionalInputProps("combobox_org_unit")}
          choices={comboBoxOptions}
          autocomplete={true}
          label={t("pages.claimsOrganizationUnit.comboBoxLabel")}
          smallLabel
        />
        {/* When the combobox is empty or a "workaround" option was selected, show an info alert */}
        <ConditionalContent visible={hasSelectedComboboxWorkaround}>
          <Alert className="measure-6" state="info" slim>
            {t("pages.claimsOrganizationUnit.followupInfo")}
          </Alert>
        </ConditionalContent>
      </Fieldset>
    </QuestionPage>
  );
};

export default withBenefitsApplication(Department);
