import React, { useState } from "react";
import withEmployerClaim, {
  WithEmployerClaimProps,
} from "../../../hoc/withEmployerClaim";
import Alert from "../../../components/core/Alert";
import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/core/Button";
import ConditionalContent from "../../../components/ConditionalContent";
import Heading from "../../../components/core/Heading";
import InputChoiceGroup from "../../../components/core/InputChoiceGroup";
import StatusRow from "../../../components/StatusRow";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import formatDateRange from "../../../utils/formatDateRange";
import { getSoonestReviewableFollowUpDate } from "../../../models/ManagedRequirement";
import { isFeatureEnabled } from "../../../services/featureFlags";
import { useTranslation } from "../../../locales/i18n";

interface PageProps extends WithEmployerClaimProps {
  appLogic: AppLogic;
  query: {
    absence_id?: string;
  };
}

export const NewApplication = (props: PageProps) => {
  const { t } = useTranslation();
  const {
    appLogic: { portalFlow },
    claim,
  } = props;
  const [formState, setFormState] = useState({
    hasReviewerVerified: "",
  });

  /**
   * This page is deprecated, but was previously linked to in email notifications to leave admins,
   * so we want to preserve the URL and redirect to the new destination.
   */
  if (isFeatureEnabled("employerShowMultiLeaveDashboard")) {
    props.appLogic.portalFlow.goToPageFor(
      "REDIRECT",
      {},
      { absence_id: props.query.absence_id },
      { redirect: true }
    );

    return null;
  }

  // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  // TODO (PORTAL-1560): Remove everything below here once we're skipping this page in production flows
  // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

  // explicitly check for false as opposed to falsy values.
  // temporarily allows the redirect behavior to work even
  // if the API has not been updated to populate the field.
  if (claim.is_reviewable === false) {
    portalFlow.goToPageFor(
      "CLAIM_NOT_REVIEWABLE",
      {},
      { absence_id: claim.fineos_absence_id },
      { redirect: true }
    );
  }

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    if (formState.hasReviewerVerified === "true") {
      portalFlow.goToNextPage({}, { absence_id: claim.fineos_absence_id });
    } else if (formState.hasReviewerVerified === "false") {
      portalFlow.goToPageFor(
        "CONFIRMATION",
        {},
        { absence_id: claim.fineos_absence_id }
      );
    }
  };

  const handleOnChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    updateFields({
      hasReviewerVerified: event.target.value,
    });
  };

  const updateFields = (fields: { [fieldName: string]: unknown }) => {
    setFormState({ ...formState, ...fields });
  };

  return (
    <React.Fragment>
      <BackButton />
      <Title>
        {t("pages.employersClaimsNewApplication.title", {
          name: claim.fullName,
        })}
      </Title>
      <Alert state="warning">
        <Trans
          i18nKey="pages.employersClaimsNewApplication.instructionsFollowUpDate"
          values={{
            date: getSoonestReviewableFollowUpDate(claim.managed_requirements),
          }}
        />
      </Alert>
      <form
        id="employer-verification-form"
        onSubmit={handleSubmit}
        className="usa-form"
        method="post"
      >
        <div className="margin-bottom-2 padding-bottom-2">
          <InputChoiceGroup
            choices={[
              {
                checked: formState.hasReviewerVerified === "true",
                label: t("pages.employersClaimsNewApplication.choiceYes"),
                value: "true",
              },
              {
                checked: formState.hasReviewerVerified === "false",
                label: t("pages.employersClaimsNewApplication.choiceNo"),
                value: "false",
              },
            ]}
            label={
              <Heading level="2">
                {t("pages.employersClaimsNewApplication.instructionsLabel")}
              </Heading>
            }
            name="hasReviewerVerified"
            onChange={handleOnChange}
            type="radio"
            smallLabel
          />
        </div>
        {!!claim.employer_dba && (
          <StatusRow
            label={t(
              "pages.employersClaimsNewApplication.organizationNameLabel"
            )}
          >
            {claim.employer_dba}
          </StatusRow>
        )}
        <StatusRow
          label={t("pages.employersClaimsNewApplication.employerIdNumberLabel")}
        >
          {claim.employer_fein}
        </StatusRow>
        <StatusRow
          label={t("pages.employersClaimsNewApplication.employeeNameLabel")}
        >
          {claim.fullName}
        </StatusRow>
        <StatusRow
          label={t("pages.employersClaimsNewApplication.ssnOrItinLabel")}
        >
          {claim.tax_identifier}
        </StatusRow>
        <StatusRow label={t("pages.employersClaimsNewApplication.dobLabel")}>
          {formatDateRange(claim.date_of_birth)}
        </StatusRow>
        <ConditionalContent
          updateFields={updateFields}
          visible={
            formState.hasReviewerVerified === "true" ||
            formState.hasReviewerVerified === "false"
          }
        >
          {formState.hasReviewerVerified === "true" && (
            <React.Fragment>
              <Heading level="2">
                {t(
                  "pages.employersClaimsNewApplication.truthAttestationHeading"
                )}
              </Heading>
              <Trans i18nKey="pages.employersClaimsNewApplication.instructions" />
              <Alert noIcon state="info">
                {t("pages.employersClaimsNewApplication.agreementBody")}
              </Alert>
            </React.Fragment>
          )}
          <Button type="submit">
            {t("pages.employersClaimsNewApplication.submitButton", {
              context:
                formState.hasReviewerVerified === "true" ? "secondary" : null,
            })}
          </Button>
        </ConditionalContent>
      </form>
    </React.Fragment>
  );
};

// TODO (PORTAL-1560): Stop wrapping this page in an HOC and just let it redirect
export default withEmployerClaim(NewApplication);
