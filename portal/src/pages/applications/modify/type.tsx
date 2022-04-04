import withUser, { WithUserProps } from "../../../hoc/withUser";
import FormLabel from "../../../components/core/FormLabel";
import PageNotFound from "../../../components/PageNotFound";
import QuestionPage from "../../../components/QuestionPage";
import React from "react";
import { isFeatureEnabled } from "../../../services/featureFlags";
import { useTranslation } from "../../../locales/i18n";

type TypeProps = WithUserProps & {
  query: {
    change_request_id: string;
  };
};

export const Type = (props: TypeProps) => {
  const changeRequestId = props.query.change_request_id;
  const { t } = useTranslation();

  /* eslint-disable require-await */
  const handleSubmit = async () => {
    // Do nothing for now
  };

  // TODO(PORTAL-2064): Remove claimantShowModifications feature flag
  if (!isFeatureEnabled("claimantShowModifications")) return <PageNotFound />;

  return (
    <QuestionPage
      title={t("pages.claimsModifyType.title")}
      onSave={handleSubmit}
    >
      <FormLabel>{t("pages.claimsModifyType.sectionLabel")}</FormLabel>
      <p>{changeRequestId}</p>
    </QuestionPage>
  );
};

export default withUser(Type);
