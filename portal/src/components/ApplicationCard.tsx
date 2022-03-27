import { filterByApplication, getLegalNotices } from "../models/Document";
import Alert from "./core/Alert";
import { AppLogic } from "../hooks/useAppLogic";
import BenefitsApplication from "../models/BenefitsApplication";
import ButtonLink from "./ButtonLink";
import Heading from "./core/Heading";
import LeaveReason from "../models/LeaveReason";
import LegalNoticeList from "./LegalNoticeList";
import React from "react";
import Spinner from "./core/Spinner";
import { Trans } from "react-i18next";
import { WithUserProps } from "src/hoc/withUser";
import { createRouteWithQuery } from "../utils/routeWithParams";
import findKeyByValue from "../utils/findKeyByValue";
import formatDate from "../utils/formatDate";
import hasDocumentsLoadError from "../utils/hasDocumentsLoadError";
import isBlank from "../utils/isBlank";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

interface ManageDocumentSectionProps {
  claim: BenefitsApplication;
}

/**
 * Section to view notices and upload documents
 */
const ManageDocumentSection = ({ claim }: ManageDocumentSectionProps) => {
  const { t } = useTranslation();
  const { fineos_absence_id: absence_id } = claim;

  const viewNoticesLink = createRouteWithQuery(
    routes.applications.status.claim,
    { absence_id },
    "view_notices"
  );

  const uploadDocumentsLink = createRouteWithQuery(
    routes.applications.status.claim,
    { absence_id },
    "upload_documents"
  );

  return (
    <div className="border-top border-base-lighter">
      <Heading className="padding-y-3" level="3" size="4">
        {t("components.applicationCard.otherActions")}
      </Heading>
      <ButtonLink
        className="display-block margin-bottom-3"
        href={viewNoticesLink}
        variation="unstyled"
      >
        {t("components.applicationCard.viewNotices")}
      </ButtonLink>

      <ButtonLink
        className="display-block margin-bottom-2"
        href={uploadDocumentsLink}
        variation="unstyled"
      >
        {t("components.applicationCard.respondToRequest")}
      </ButtonLink>
    </div>
  );
};

interface LegalNoticeSectionProps {
  appLogic: AppLogic;
  claim: BenefitsApplication;
}

/**
 * Section to view legal notices for in-progress applications.
 * There are 2 main use cases for in-progress applications receiving notices:
 *    1. Withdrawing a pending application –> Withdrawn notice
 *    2. The contact center may deny in-progress application they can see that's open for a certain length of time -> Denial notice
 */
const LegalNoticeSection = (props: LegalNoticeSectionProps) => {
  const { t } = useTranslation();
  const showNotices = props.claim.status === "Submitted";
  const {
    documents: { loadAll, isLoadingClaimDocuments },
  } = props.appLogic;

  React.useEffect(() => {
    if (showNotices) {
      loadAll(props.claim.application_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadAll]);

  const shouldShowSpinner =
    isLoadingClaimDocuments(props.claim.application_id) &&
    !hasDocumentsLoadError(props.appLogic.errors, props.claim.application_id);

  if (!showNotices) return null;

  // check for spinner before documents length, since length is 0 while loading.
  if (shouldShowSpinner) {
    return (
      <div className="text-center">
        <Spinner
          small
          aria-label={t("components.applicationCard.loadingLabel")}
        />
      </div>
    );
  }

  const legalNotices = getLegalNotices(
    filterByApplication(
      props.appLogic.documents.documents.items,
      props.claim.application_id
    )
  );

  if (!legalNotices.length) return null;

  return (
    <div className="margin-top-2 padding-bottom-1" style={{ maxWidth: 385 }}>
      <Heading level="3">{t("components.applicationCard.viewNotices")}</Heading>
      <LegalNoticeList
        onDownloadClick={props.appLogic.documents.download}
        documents={filterByApplication(
          props.appLogic.documents.documents.items,
          props.claim.application_id
        )}
        {...props}
      />
    </div>
  );
};

interface InProgressStatusCardProps {
  claim: BenefitsApplication;
  appLogic: AppLogic;
}

/**
 * Status card for claim.status != "Completed" (In Progress)
 */
const InProgressStatusCardActions = (props: InProgressStatusCardProps) => {
  const { claim } = props;
  const { t } = useTranslation();

  const showSubmitAllPartsText = isBlank(props.claim.employer_fein);
  return (
    <React.Fragment>
      {showSubmitAllPartsText && (
        <p>{t("components.applicationCard.inProgressText")}</p>
      )}
      <LegalNoticeSection {...props} />
      <div className="border-top border-base-lighter padding-top-2">
        <ButtonLink
          className="display-flex flex-align-center flex-justify-center flex-column margin-right-0"
          href={createRouteWithQuery(routes.applications.checklist, {
            claim_id: claim.application_id,
          })}
        >
          <div>{t("components.applicationCard.continueApplication")}</div>
        </ButtonLink>
      </div>
    </React.Fragment>
  );
};

interface CompletedStatusCardProps {
  claim: BenefitsApplication;
}

/**
 * Status card for claim.status = "Completed"
 */
const CompletedStatusCardActions = ({ claim }: CompletedStatusCardProps) => {
  const { t } = useTranslation();

  const statusPageLink = createRouteWithQuery(
    routes.applications.status.claim,
    { absence_id: claim.fineos_absence_id }
  );

  return (
    <React.Fragment>
      <div className="border-top border-base-lighter padding-y-2 margin-y-2 margin-bottom-0">
        <ButtonLink
          className="width-full display-flex flex-align-center flex-justify-center flex-column margin-right-0"
          href={statusPageLink}
        >
          {t("components.applicationCard.viewStatusUpdatesAndDetails")}
        </ButtonLink>
      </div>
      <ManageDocumentSection claim={claim} />
    </React.Fragment>
  );
};

interface ApplicationCardProps extends WithUserProps {
  claim: BenefitsApplication;
  successfullyImported: boolean;
}

/**
 * Main entry point for an existing benefits Application, allowing
 * claimants to continue an in progress application, view what
 * they've submitted, view notices and instructions, or upload
 * additional docs.
 */
export const ApplicationCard = (props: ApplicationCardProps) => {
  const { t } = useTranslation();
  const { claim, successfullyImported } = props;

  return (
    <div className="maxw-mobile-lg margin-bottom-3">
      <div
        className={`border-top-1 ${
          claim.status === "Completed" ? "border-primary" : "border-gold"
        }`}
      />
      <article className="border-x border-bottom border-base-lighter padding-2 padding-top-3">
        {successfullyImported && (
          <Alert state="success">
            <p>
              {t("components.applicationCard.claimAssociatedSuccessfully", {
                fineos_absence_id: claim.fineos_absence_id,
              })}
            </p>
          </Alert>
        )}
        {claim.isEarliestSubmissionDateInFuture && (
          <Alert state="warning" noIcon>
            <p>
              <Trans
                i18nKey="components.applicationCard.earliestSubmissionDateInFuture"
                values={{
                  earliest_submission_date: formatDate(
                    claim.computed_earliest_submission_date
                  ).short(),
                }}
              />
            </p>
          </Alert>
        )}
        <Heading level="2">
          {t("components.applicationCard.heading", {
            context:
              findKeyByValue(LeaveReason, claim.leave_details?.reason) ??
              "noReason",
          })}
        </Heading>
        {claim.fineos_absence_id && (
          <p>
            {t("components.applicationCard.applicationID")}
            <br />
            <strong>{claim.fineos_absence_id}</strong>
          </p>
        )}

        {claim.leaveStartDate && claim.leaveEndDate && (
          <p>
            {t("components.applicationCard.leaveDatesLabel")}
            <br />
            <strong>
              {t("components.applicationCard.leaveDates", {
                start: formatDate(claim.leaveStartDate).short(),
                end: formatDate(claim.leaveEndDate).short(),
              })}
            </strong>
          </p>
        )}

        {claim.employer_fein && (
          <p>
            {t("components.applicationCard.employerEIN")}
            <br />
            <strong>{claim.employer_fein}</strong>
          </p>
        )}
        {claim.status === "Completed" ? (
          <CompletedStatusCardActions {...props} />
        ) : (
          <InProgressStatusCardActions {...props} />
        )}
      </article>
    </div>
  );
};

export default ApplicationCard;
