import withUser, { WithUserProps } from "../../../hoc/withUser";
import FormLabel from "../../../components/core/FormLabel";
import PageNotFound from "../../../components/PageNotFound";
import QuestionPage from "../../../components/QuestionPage";
import React from "react";
import { isFeatureEnabled } from "../../../services/featureFlags";
import { useTranslation } from "../../../locales/i18n";

type ReviewProps = WithUserProps & {
  query: {
    change_request_id: string;
  };
};

export const Review = (props: ReviewProps) => {
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
      title={t("pages.claimsModifyReview.title")}
      onSave={handleSubmit}
    >
      <FormLabel>{t("pages.claimsModifyReview.sectionLabel")}</FormLabel>
      <p>{changeRequestId}</p>
    </QuestionPage>
  );
};

export default withUser(Review);
