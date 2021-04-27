import BenefitsApplication, {
  CaringLeaveMetadata,
  RelationshipToCaregiver,
} from "../../models/BenefitsApplication";
import { get, pick } from "lodash";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
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
        hint={t("pages.claimsFamilyMemberRelationship.sectionHint")}
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
