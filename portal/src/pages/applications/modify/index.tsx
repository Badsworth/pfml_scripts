import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../../hoc/withBenefitsApplication";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/core/Button";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import Title from "../../../components/core/Title";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

type IndexProps = WithBenefitsApplicationProps & {
  query: {
    claim_id: string;
  };
};

export const Index = (props: IndexProps) => {
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
        label={t("pages.claimsModifyIndex.backButtonLabel")}
        href={routes.applications.index}
      />
      <form onSubmit={handleSubmit} className="usa-form">
        <Title>{t("pages.claimsModifyIndex.title")}</Title>
        <p>{claimId}</p>
        <Button className="margin-top-4" type="submit">
          {t("pages.claimsModifyIndex.button")}
        </Button>
      </form>
    </React.Fragment>
  );
};

export default withBenefitsApplication(Index);
