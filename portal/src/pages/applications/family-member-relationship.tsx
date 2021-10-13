import BenefitsApplication, {
  CaringLeaveMetadata,
  RelationshipToCaregiver,
} from "../../models/BenefitsApplication";
import { get, pick } from "lodash";
import Details from "../../components/Details";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

const caringLeaveMetadataKey = "leave_details.caring_leave_metadata";

export const fields = [
  `claim.${caringLeaveMetadataKey}.relationship_to_caregiver`,
];

export const FamilyMemberRelationship = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
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
    const updatedData = pick({ claim: formState }, fields).claim;
    await appLogic.benefitsApplications.update(
      claim.application_id,
      updatedData
    );
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const relationshipList = [
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
              // @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: Element; label: string; classNam... Remove this comment to see the full error message
              className="text-bold"
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

FamilyMemberRelationship.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withBenefitsApplication(FamilyMemberRelationship);
