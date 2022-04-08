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

type ChecklistProps = WithBenefitsApplicationProps & {
  query: {
    change_request_id: string;
  };
};

export const Checklist = (props: ChecklistProps) => {
  const changeRequestId = props.query.change_request_id;
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
        label={t("pages.claimsModifyChecklist.backButtonLabel")}
        href={routes.applications.index}
      />
      <form onSubmit={handleSubmit} className="usa-form">
        <Title>{t("pages.claimsModifyChecklist.title")}</Title>
        <p>{changeRequestId}</p>
      </form>
    </React.Fragment>
  );
};

export default withBenefitsApplication(Checklist);
