import {
  CaringLeaveMetadata,
  RelationshipToCaregiver,
} from "../../models/BenefitsApplication";
import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Details from "../../components/core/Details";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

const caringLeaveMetadataKey = "leave_details.caring_leave_metadata";

export const fields = [
  `claim.${caringLeaveMetadataKey}.relationship_to_caregiver`,
];

export const FamilyMemberRelationship = (
  props: WithBenefitsApplicationProps
) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  const { formState, updateFields } = useFormState({
    leave_details: {
      caring_leave_metadata: new CaringLeaveMetadata(
        get(props.claim, caringLeaveMetadataKey)
      ),
    },
  });

  const relationship = get(
    formState,
    `${caringLeaveMetadataKey}.relationship_to_caregiver`
  );
  const handleSave = async () => {
    const updatedData = pick({ claim: formState }, fields).claim || {};
    await appLogic.benefitsApplications.update(
      claim.application_id,
      updatedData
    );
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const relationshipList: Array<keyof typeof RelationshipToCaregiver> = [
    "child",
    "spouse",
    "parent",
    "inlaw",
    "sibling",
    "grandchild",
    "grandparent",
  ];

  return (
    <QuestionPage
      title={t("pages.claimsLeaveReason.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps(
          "leave_details.caring_leave_metadata.relationship_to_caregiver"
        )}
        choices={relationshipList.map((key) => ({
          checked: relationship === RelationshipToCaregiver[key],
          label: t("pages.claimsFamilyMemberRelationship.choiceLabel", {
            context: key,
          }),
          value: RelationshipToCaregiver[key],
        }))}
        label={t("pages.claimsFamilyMemberRelationship.sectionLabel")}
        hint={
          <React.Fragment>
            <Trans
              i18nKey="pages.claimsFamilyMemberRelationship.sectionHint"
              components={{
                "caregiver-relationship-link": (
                  <a
                    target="_blank"
                    rel="noopener"
                    href={routes.external.massgov.caregiverRelationship}
                  />
                ),
              }}
            />
            <Details
              label={t("pages.claimsFamilyMemberRelationship.detailsLabel")}
            >
              <Trans
                i18nKey="pages.claimsFamilyMemberRelationship.detailsBody"
                components={{
                  "in-loco-parentis-link": (
                    <a
                      target="_blank"
                      rel="noopener"
                      href={routes.external.inLocoParentis}
                    />
                  ),
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                }}
              />
            </Details>
          </React.Fragment>
        }
        type="radio"
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(FamilyMemberRelationship);
