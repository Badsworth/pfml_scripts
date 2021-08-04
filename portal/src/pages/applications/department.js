import React, { useEffect, useState } from "react";

import Alert from "../../components/Alert";
import BenefitsApplication from "../../models/BenefitsApplication";
import ComboBox from "../../components/ComboBox";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../../components/Details";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
// import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.org_unit", "claim.org_unit_radio"];

const allDepartments = [
  {
    department_id: 1,
    department_description: "HR",
  },
  {
    department_id: 2,
    department_description: "DFML",
  },
  {
    department_id: 3,
    department_description: "Contact Center",
  },
  {
    department_id: 4,
    department_description: "DevOps",
  },
  {
    department_id: 5,
    department_description: "DevOps2",
  },
  {
    department_id: 6,
    department_description: "DevOps3",
  },
];

export const Department = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  // const showDepartments = isFeatureEnabled("claimantShowDepartments");

  const initialFormState = pick(props, fields).claim;

  const { formState, updateFields } = useFormState(initialFormState);

  // if (!showDepartments) {
  // @todo: go to next page and ignore departments, auto-select "I'm not sure"
  // }

  const handleSave = () => {
    // If user selects a workaround, then take the combobox's value
    // otherwise, take the radio group's value
    const finalDepartmentDecision = hasSelectedRadioWorkaround
      ? formState.org_unit
      : formState.org_unit_radio;

    formState.org_unit = finalDepartmentDecision;

    console.log(formState);
    if (!finalDepartmentDecision) {
      console.error("Invalid department", { finalDepartmentDecision });
    } else {
      console.log("Selected " + formState.org_unit);
      appLogic.benefitsApplications.update(claim.application_id, formState);
    }
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const [departments, setDepartments] = useState([]);
  const [employerDepartments, setEmployerDepartments] = useState([]);

  const workarounds = [
    t("pages.claimsDepartment.choiceNotListed"),
    t("pages.claimsDepartment.choiceNotSure"),
  ];

  const hasSelectedRadioWorkaround = [...workarounds, "No"].includes(
    formState.org_unit_radio
  );
  const hasSelectedComboboxWorkaround = workarounds.includes(
    formState.org_unit
  );

  // API calls
  const populateDepartments = async () => {
    // obtain the full list of departments connected to this claimant
    if (departments.length < 1) {
      // const deps = await appLogic.benefitsApplications.getDepartments();
      const deps = [
        allDepartments[0],
        // allDepartments[1],
        // allDepartments[2],
      ];
      setDepartments(deps);
    }
    // obtain the full list of departments connected to this claimant's employer
    if (employerDepartments.length < 1) {
      // const deps = await appLogic.benefitsApplications.getDepartmentsByEmployer(claim.employer_fein)
      const deps = await allDepartments;
      setEmployerDepartments(deps);
    }
  };

  const getDepartmentListSizes = (deps) => {
    const isLong = deps.length > 5;
    const isShort = deps.length > 1 && deps.length <= 5;
    const isUnique = deps.length === 1;
    return {
      isLong,
      isShort,
      isUnique,
    };
  };

  const getDepartmentChoices = (deps) => {
    if (deps.length < 1) return [];

    const { isLong, isShort, isUnique } = getDepartmentListSizes(deps);

    const departmentChoices = deps.map((dep) => ({
      label: dep.department_description,
      value: dep.department_description,
      checked: dep.department_description === formState.org_unit_radio,
    }));

    // @todo: value cannot be a translated label text
    const workaroundChoices = workarounds.map((wa) => ({
      label: wa,
      value: wa,
      checked: wa === formState.org_unit_radio,
    }));

    if (isLong || isShort) {
      return [...departmentChoices, ...workaroundChoices];
    }
    if (isUnique) {
      return [
        {
          label: t("pages.claimsDepartment.choiceYes"),
          value: deps[0]?.department_description,
        },
        {
          label: t("pages.claimsDepartment.choiceNo"),
          value: "No",
        },
      ];
    }
  };

  const { isLong, isShort, isUnique } = getDepartmentListSizes(departments);
  const claimantChoices = getDepartmentChoices(departments);
  const employerChoices = getDepartmentChoices(employerDepartments);

  useEffect(() => {
    populateDepartments();
    return () => null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <ConditionalContent visible={isUnique}>
        <InputChoiceGroup
          {...getFunctionalInputProps("org_unit_radio")}
          choices={claimantChoices}
          label={t("pages.claimsDepartment.confirmSectionLabel")}
          hint={
            <Trans
              i18nKey="pages.claimsDepartment.confirmHint"
              tOptions={{ department: departments[0]?.department_description }}
            />
          }
          type="radio"
        >
          <div className="margin-top-2">
            <Details label={t("pages.claimsDepartment.moreThanOne")}>
              {t("pages.claimsDepartment.hint")}
            </Details>
          </div>
        </InputChoiceGroup>
      </ConditionalContent>

      <ConditionalContent visible={isShort}>
        <InputChoiceGroup
          {...getFunctionalInputProps("org_unit_radio", {
            fallbackValue: formState.org_unit_radio || "",
          })}
          choices={claimantChoices}
          label={t("pages.claimsDepartment.sectionLabel")}
          hint={t("pages.claimsDepartment.hint")}
          type="radio"
        />
      </ConditionalContent>

      <ConditionalContent visible={isLong || hasSelectedRadioWorkaround}>
        <Fieldset>
          <ConditionalContent visible={isLong}>
            <FormLabel
              component="legend"
              hint={t("pages.claimsDepartment.hint")}
            >
              {t("pages.claimsDepartment.sectionLabel")}
            </FormLabel>
          </ConditionalContent>
          <ComboBox
            {...getFunctionalInputProps("org_unit", {
              fallbackValue: formState.org_unit || "",
            })}
            choices={
              hasSelectedRadioWorkaround ? employerChoices : claimantChoices
            }
            label={t("pages.claimsDepartment.comboBoxLabel")}
            smallLabel
            required
          />
          <ConditionalContent visible={hasSelectedComboboxWorkaround}>
            <Alert className="measure-6" state="info" noIcon>
              {t("pages.claimsDepartment.followupInfo")}
            </Alert>
          </ConditionalContent>
        </Fieldset>
      </ConditionalContent>
    </QuestionPage>
  );
};

Department.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(Department);
