import BenefitsApplication, {
  ReasonQualifier as ReasonQualifierEnum,
} from "../../models/BenefitsApplication";
import { get, pick, set } from "lodash";
import Alert from "../../components/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../../components/Details";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveReasonEnum from "../../models/LeaveReason";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [
  "claim.leave_details.reason",
  "claim.leave_details.reason_qualifier",
];

export const LeaveReason = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
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
    // when the claimant changes the answer, clear out pregnant_or_recent_birth field
    if (reason !== get(claim, "leave_details.reason")) {
      set(formState, "leave_details.pregnant_or_recent_birth", null);
    }

    await appLogic.benefitsApplications.update(claim.application_id, formState);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const choiceMedical = {
    checked: [LeaveReasonEnum.medical, LeaveReasonEnum.pregnancy].includes(
      reason
    ),
    label: t("pages.claimsLeaveReason.medicalLeaveLabel"),
    value: LeaveReasonEnum.medical,
  };

  const choiceBonding = {
    checked: reason === LeaveReasonEnum.bonding,
    label: t("pages.claimsLeaveReason.bondingLeaveLabel"),
    value: LeaveReasonEnum.bonding,
  };

  const choiceActiveDutyFamily = {
    // TODO (CP-515): We need to more accurately map this Family Leave option to signify that
    // this is active duty family leave, as opposed to another family leave type.
    checked: reason === LeaveReasonEnum.activeDutyFamily,
    label: t("pages.claimsLeaveReason.activeDutyFamilyLeaveLabel"),
    value: LeaveReasonEnum.activeDutyFamily,
  };

  const choiceServiceMemberFamily = {
    // TODO (CP-515): We need to more accurately map this Family Leave option to signify that
    // this is family leave to care for a service member, as opposed to another family leave type.
    checked: reason === LeaveReasonEnum.serviceMemberFamily,
    label: t("pages.claimsLeaveReason.serviceMemberFamilyLeaveLabel"),
    value: LeaveReasonEnum.serviceMemberFamily,
  };

  const choiceCaringLeave = {
    checked: reason === LeaveReasonEnum.care,
    label: t("pages.claimsLeaveReason.caringLeaveLabel"),
    value: LeaveReasonEnum.care,
  };

  // Military leave types are disabled for soft launch (CP-1145)
  // TODO (CP-534): Remove this feature flag when the portal supports
  // activeDutyFamily and serviceMemberFamily
  const showMilitaryLeaveTypes = isFeatureEnabled(
    "claimantShowMilitaryLeaveTypes"
  );

  const getChoices = () => {
    const choices = [choiceMedical, choiceBonding, choiceCaringLeave];

    showMilitaryLeaveTypes &&
      choices.push(choiceActiveDutyFamily, choiceServiceMemberFamily);

    return choices;
  };

  return (
    <QuestionPage
      title={t("pages.claimsLeaveReason.title")}
      onSave={handleSave}
    >
      {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: Element; state: string; neutral:... Remove this comment to see the full error message */}
      <Alert state="info" neutral>
        <Trans
          i18nKey="pages.claimsLeaveReason.alertBody"
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
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

      <InputChoiceGroup
        {...getFunctionalInputProps("leave_details.reason")}
        choices={getChoices()}
        label={t("pages.claimsLeaveReason.sectionLabel")}
        hint={t("pages.claimsLeaveReason.sectionHint")}
        type="radio"
      />

      <ConditionalContent
        visible={
          claim.previous_leaves_same_reason.length > 0 &&
          claim.leave_details.reason !== reason
        }
      >
        {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: Element; state: string; heading:... Remove this comment to see the full error message */}
        <Alert
          state="warning"
          heading={t("pages.claimsLeaveReason.leaveReasonChangedAlertTitle")}
        >
          <Trans i18nKey="pages.claimsLeaveReason.leaveReasonChangedAlertBody" />
        </Alert>
      </ConditionalContent>

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
              <Trans
                i18nKey="pages.claimsLeaveReason.bondingTypeMultipleBirthsDetailsSummary"
                components={{
                  "multiple-births-link": (
                    <a
                      target="_blank"
                      rel="noopener"
                      href={routes.external.massgov.multipleBirths}
                    />
                  ),
                }}
              />
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
  claim: PropTypes.instanceOf(BenefitsApplication),
  appLogic: PropTypes.object.isRequired,
};

export default withBenefitsApplication(LeaveReason);
