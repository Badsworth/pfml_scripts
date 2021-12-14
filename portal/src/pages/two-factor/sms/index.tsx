import { AppLogic } from "../../../hooks/useAppLogic";

import InputChoiceGroup from "../../../components/core/InputChoiceGroup";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import ThrottledButton from "src/components/ThrottledButton";
import { Trans } from "react-i18next";
import User from "src/models/User";
import { get } from "lodash";
import { isFeatureEnabled } from "../../../services/featureFlags";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

interface IndexSMSProps {
  appLogic: AppLogic;
  user: User;
}

export const IndexSMS = (props: IndexSMSProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    enterMFASetupFlow: null,
  });

  const handleSubmit = async () => {
    if (formState.enterMFASetupFlow) {
      await appLogic.portalFlow.goToPageFor("EDIT_MFA_PHONE");
    } else {
      await appLogic.users.updateUser(props.user.user_id, {
        mfa_delivery_preference: "Opt Out",
      });
    }
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // TODO(PORTAL-1007): Remove claimantShowMFA feature flag
  if (!isFeatureEnabled("claimantShowMFA")) return <PageNotFound />;

  return (
    <form className="usa-form">
      <InputChoiceGroup
        {...getFunctionalInputProps("enterMFASetupFlow")}
        label={t("pages.authTwoFactorSmsIndex.title")}
        hint={<Trans i18nKey="pages.authTwoFactorSmsIndex.hint" />}
        choices={[
          {
            checked: get(formState, "enterMFASetupFlow") === true,
            label: t("pages.authTwoFactorSmsIndex.optIn"),
            value: "true",
          },
          {
            checked: get(formState, "enterMFASetupFlow") === false,
            label: t("pages.authTwoFactorSmsIndex.optOut"),
            value: "false",
          },
        ]}
        type="radio"
      />
      <ThrottledButton
        type="submit"
        className="display-block"
        onClick={handleSubmit}
      >
        {t("pages.authTwoFactorSmsIndex.saveButton")}
      </ThrottledButton>
    </form>
  );
};

export default withUser(IndexSMS);
