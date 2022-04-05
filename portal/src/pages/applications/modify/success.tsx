import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../../hoc/withBenefitsApplication";
import BackButton from "../../../components/BackButton";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import Title from "../../../components/core/Title";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

type SuccessProps = WithBenefitsApplicationProps & {
  query: {
    claim_id: string;
  };
};

export const Success = (props: SuccessProps) => {
  const claimId = props.query.claim_id;
  const { t } = useTranslation();

  /* eslint-disable require-await */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    // Do nothing for now
  };

  // TODO(PORTAL-2064): Remove claimantShowModifications feature flag
  if (!isFeatureEnabled("claimantShowModifications")) return <PageNotFound />;

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsModifySuccess.backButtonLabel")}
        href={routes.applications.index}
      />
      <form onSubmit={handleSubmit} className="usa-form">
        <Title>{t("pages.claimsModifySuccess.title")}</Title>
        <p>{claimId}</p>
      </form>
    </React.Fragment>
  );
};

export default withBenefitsApplication(Success);
