import { AppLogic } from "../../../hooks/useAppLogic";

import InputChoiceGroup from "../../../components/core/InputChoiceGroup";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import ThrottledButton from "src/components/ThrottledButton";
import { Trans } from "react-i18next";
import User from "src/models/User";
import { ValidationError } from "../../../errors";
import { get } from "lodash";
import { isFeatureEnabled } from "../../../services/featureFlags";
import tracker from "../../../services/tracker";
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

  const showNoValueSelectedError = (appLogic: AppLogic) => {
    const validation_issue = {
      field: "enterMFASetupFlow",
      type: "required",
      namespace: "mfa",
    };
    appLogic.catchError(new ValidationError([validation_issue]));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    // Show an error and dont leave the page when no value selected
    event.preventDefault();
    appLogic.clearErrors();
    if (formState.enterMFASetupFlow === null) {
      showNoValueSelectedError(appLogic);
      return;
    }

    if (formState.enterMFASetupFlow) {
      tracker.trackEvent("User entered MFA setup flow");
      await appLogic.portalFlow.goToPageFor("EDIT_MFA_PHONE");
    } else {
      tracker.trackEvent("User opted out of MFA");
      await appLogic.users.updateUser(props.user.user_id, {
        mfa_delivery_preference: "Opt Out",
      });
      appLogic.portalFlow.goToPageFor("CONTINUE");
    }
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
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
