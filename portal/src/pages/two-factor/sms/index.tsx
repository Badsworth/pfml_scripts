import { AppLogic } from "../../../hooks/useAppLogic";

import Button from "../../../components/core/Button";
import InputChoiceGroup from "../../../components/core/InputChoiceGroup";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import { Trans } from "react-i18next";
import { get } from "lodash";
import { isFeatureEnabled } from "../../../services/featureFlags";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

interface IndexSMSProps {
  appLogic: AppLogic;
}

export const IndexSMS = (props: IndexSMSProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    enterMFASetupFlow: null,
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    // Do nothing for now
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // TODO(PORTAL-1007): Remove claimantShowMFA feature flag
  if (!isFeatureEnabled("claimantShowMFA")) return <PageNotFound />;

  return (
    <form className="usa-form" onSubmit={handleSubmit} method="post">
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
      <Button type="submit" className="display-block">
        {t("pages.authTwoFactorSmsIndex.saveButton")}
      </Button>
    </form>
  );
};

export default withUser(IndexSMS);
