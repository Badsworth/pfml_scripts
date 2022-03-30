import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = [
  "claim.additional_user_not_found_info.recently_acquired_or_merged",
];

export const RecentlyAcquiredOrMerged = (
  props: WithBenefitsApplicationProps
) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  console.log(claim);
  const { formState, updateFields } = useFormState({
    recently_acquired_or_merged:
      get(
        claim,
        "additional_user_not_found_info.recently_acquired_or_merged"
      ) ?? null,
  });

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, {
      additional_user_not_found_info: {
        ...formState,
      },
    });

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const recently_acquired_or_merged = get(
    formState,
    "recently_acquired_or_merged"
  );
  console.log(recently_acquired_or_merged);
  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      dataCy="additional-user-not-found-info-form"
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("recently_acquired_or_merged")}
        choices={[
          {
            checked: recently_acquired_or_merged === true,
            label: t(
              "pages.claimsAdditionalUserNotFoundInfo.recentlyAcquiredOrMergedYesLabel"
            ),
            value: "true",
          },
          {
            checked: recently_acquired_or_merged === false,
            label: t(
              "pages.claimsAdditionalUserNotFoundInfo.recentlyAcquiredOrMergedNoLabel"
            ),
            value: "false",
          },
          {
            checked:
              recently_acquired_or_merged === null ||
              recently_acquired_or_merged === "",
            label: t(
              "pages.claimsAdditionalUserNotFoundInfo.recentlyAcquiredOrMergedIDontKnowLabel"
            ),
            value: "",
          },
        ]}
        type="radio"
        label={t(
          "pages.claimsAdditionalUserNotFoundInfo.recentlyAcquiredOrMergedLabel"
        )}
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(RecentlyAcquiredOrMerged);
