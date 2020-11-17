import Claim, {
  LeaveReason as LeaveReasonEnum,
  ReasonQualifier as ReasonQualifierEnum,
} from "../../models/Claim";
import { Trans, useTranslation } from "react-i18next";
import { get, pick, set } from "lodash";
import Alert from "../../components/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../../components/Details";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.leave_details.reason",
  "claim.leave_details.reason_qualifier",
];

export const LeaveReason = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );
  const reason = get(formState, "leave_details.reason");
  const reason_qualifier = get(formState, "leave_details.reason_qualifier");

  const handleSave = async () => {
    if (reason !== LeaveReasonEnum.bonding) {
      set(formState, "leave_details.child_birth_date", null);
      set(formState, "leave_details.child_placement_date", null);
      set(formState, "leave_details.has_future_child_date", null);
    }

    await appLogic.claims.update(claim.application_id, formState);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const choiceMedical = {
    checked: reason === LeaveReasonEnum.medical,
    hint: t("pages.claimsLeaveReason.medicalLeaveHint"),
    label: t("pages.claimsLeaveReason.medicalLeaveLabel"),
    value: LeaveReasonEnum.medical,
  };

  const choiceBonding = {
    checked: reason === LeaveReasonEnum.bonding,
    hint: t("pages.claimsLeaveReason.bondingLeaveHint"),
    label: t("pages.claimsLeaveReason.bondingLeaveLabel"),
    value: LeaveReasonEnum.bonding,
  };

  const choiceActiveDutyFamily = {
    // TODO (CP-515): We need to more accurately map this Family Leave option to signify that
    // this is active duty family leave, as opposed to another family leave type.
    checked: reason === LeaveReasonEnum.activeDutyFamily,
    hint: t("pages.claimsLeaveReason.activeDutyFamilyLeaveHint"),
    label: t("pages.claimsLeaveReason.activeDutyFamilyLeaveLabel"),
    value: LeaveReasonEnum.activeDutyFamily,
  };

  const choiceServiceMemberFamily = {
    // TODO (CP-515): We need to more accurately map this Family Leave option to signify that
    // this is family leave to care for a service member, as opposed to another family leave type.
    checked: reason === LeaveReasonEnum.serviceMemberFamily,
    hint: t("pages.claimsLeaveReason.serviceMemberFamilyLeaveHint"),
    label: t("pages.claimsLeaveReason.serviceMemberFamilyLeaveLabel"),
    value: LeaveReasonEnum.serviceMemberFamily,
  };

  // Medical leave type is disabled for soft launch (CP-1245)
  // TODO (CP-1246): Remove this feature flag when the portal supports medical
  const showMedicalLeaveType = isFeatureEnabled("claimantShowMedicalLeaveType");

  // Military leave types are disabled for soft launch (CP-1145)
  // TODO (CP-534): Remove this feature flag when the portal supports
  // activeDutyFamily and serviceMemberFamily
  const showMilitaryLeaveTypes = isFeatureEnabled(
    "claimantShowMilitaryLeaveTypes"
  );

  const getChoices = () => {
    const choices = [];

    showMedicalLeaveType && choices.push(choiceMedical);
    choices.push(choiceBonding);
    showMilitaryLeaveTypes &&
      choices.push(choiceActiveDutyFamily, choiceServiceMemberFamily);

    return choices;
  };

  return (
    <QuestionPage
      title={t("pages.claimsLeaveReason.title")}
      onSave={handleSave}
    >
      {(!showMilitaryLeaveTypes || !showMedicalLeaveType) && (
        <Alert state="info" neutral>
          <Trans
            i18nKey="pages.claimsLeaveReason.alertBody"
            components={{
              "mass-benefits-guide-serious-health-condition": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={
                    routes.external.massgov.benefitsGuide_seriousHealthCondition
                  }
                />
              ),
              p: <p />,
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
          />
        </Alert>
      )}

      <InputChoiceGroup
        {...getFunctionalInputProps("leave_details.reason")}
        choices={getChoices()}
        label={t("pages.claimsLeaveReason.sectionLabel")}
        hint={t("pages.claimsLeaveReason.sectionHint")}
        type="radio"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={["leave_details.reason_qualifier"]}
        getField={getField}
        clearField={clearField}
        updateFields={updateFields}
        visible={reason === LeaveReasonEnum.bonding}
      >
        <InputChoiceGroup
          {...getFunctionalInputProps("leave_details.reason_qualifier")}
          hint={
            <Details
              label={t(
                "pages.claimsLeaveReason.bondingTypeMultipleBirthsDetailsLabel"
              )}
            >
              {t(
                "pages.claimsLeaveReason.bondingTypeMultipleBirthsDetailsSummary"
              )}
            </Details>
          }
          choices={[
            {
              checked: reason_qualifier === ReasonQualifierEnum.newBorn,
              label: t("pages.claimsLeaveReason.bondingTypeNewbornLabel"),
              value: ReasonQualifierEnum.newBorn,
            },
            {
              checked: reason_qualifier === ReasonQualifierEnum.adoption,
              label: t("pages.claimsLeaveReason.bondingTypeAdoptionLabel"),
              value: ReasonQualifierEnum.adoption,
            },
            {
              checked: reason_qualifier === ReasonQualifierEnum.fosterCare,
              label: t("pages.claimsLeaveReason.bondingTypeFosterLabel"),
              value: ReasonQualifierEnum.fosterCare,
            },
          ]}
          label={t("pages.claimsLeaveReason.bondingTypeLabel")}
          type="radio"
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

LeaveReason.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(LeaveReason);
