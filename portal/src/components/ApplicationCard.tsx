import { filterByApplication, getLegalNotices } from "../models/Document";
import { AppLogic } from "../hooks/useAppLogic";
import BenefitsApplication from "../models/BenefitsApplication";
import ButtonLink from "./ButtonLink";
import Heading from "./core/Heading";
import LeaveReason from "../models/LeaveReason";
import LegalNoticeList from "./LegalNoticeList";
import React from "react";
import Spinner from "./core/Spinner";
import Tag from "./core/Tag";
import { WithUserProps } from "src/hoc/withUser";
import { createRouteWithQuery } from "../utils/routeWithParams";
import findKeyByValue from "../utils/findKeyByValue";
import hasDocumentsLoadError from "../utils/hasDocumentsLoadError";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

interface HeaderSectionProps {
  title: string;
}

/**
 * Main header for the top of status cards
 */
const HeaderSection = ({ title }: HeaderSectionProps) => (
  <Heading className="padding-top-3" level="3" size="2">
    {title}
  </Heading>
);

interface TitleAndDetailSectionItemProps {
  details: string;
  title: string;
}

/**
 * Group together details for status cards
 */
const TitleAndDetailSectionItem = ({
  details,
  title,
}: TitleAndDetailSectionItemProps) => (
  <div className="padding-y-1">
    <p>{title}</p>
    <p className="margin-top-05 text-bold">{details}</p>
  </div>
);

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
      <Heading className="padding-y-3" level="4">
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
 * Section to view legal notices for in-progress applications
 */
const LegalNoticeSection = (props: LegalNoticeSectionProps) => {
  const { t } = useTranslation();
  const isSubmitted = props.claim.status === "Submitted";
  const {
    documents: { loadAll, isLoadingClaimDocuments },
  } = props.appLogic;

  React.useEffect(() => {
    loadAll(props.claim.application_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadAll]);

  const shouldShowSpinner =
    isLoadingClaimDocuments(props.claim.application_id) &&
    !hasDocumentsLoadError(
      props.appLogic.appErrors,
      props.claim.application_id
    );

  /**
   * If application is not submitted,
   * don't display section
   */
  if (!isSubmitted) return null;

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
  number: number;
  appLogic: AppLogic;
}

/**
 * Status card for claim.status != "Completed" (In Progress)
 */
const InProgressStatusCard = (props: InProgressStatusCardProps) => {
  const { claim, number } = props;
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <HeaderSection
        title={t("components.applicationCard.heading", {
          number,
        })}
      />
      <Tag
        state="warning"
        label={t("components.applicationCard.inProgressTag")}
      />
      <p>{t("components.applicationCard.inProgressText")}</p>
      {claim.employer_fein && (
        <TitleAndDetailSectionItem
          title={t("components.applicationCard.employerEIN")}
          details={claim.employer_fein}
        />
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
const CompletedStatusCard = ({ claim }: CompletedStatusCardProps) => {
  const { t } = useTranslation();

  const leaveReasonText = t("components.applicationCard.leaveReasonValue", {
    context: findKeyByValue(LeaveReason, claim.leave_details?.reason),
  });

  const statusPageLink = createRouteWithQuery(
    routes.applications.status.claim,
    { absence_id: claim.fineos_absence_id }
  );

  return (
    <React.Fragment>
      <HeaderSection title={leaveReasonText} />
      <TitleAndDetailSectionItem
        title={t("components.applicationCard.applicationID")}
        details={claim.fineos_absence_id || ""}
      />
      <TitleAndDetailSectionItem
        title={t("components.applicationCard.employerEIN")}
        details={claim.employer_fein || ""}
      />

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
  number: number;
}

/**
 * Main entry point for an existing benefits Application, allowing
 * claimants to continue an in progress application, view what
 * they've submitted, view notices and instructions, or upload
 * additional docs.
 */
export const ApplicationCard = (props: ApplicationCardProps) => {
  const {
    claim: { status },
  } = props;

  return (
    <div className="maxw-mobile-lg margin-bottom-3">
      <div
        className={`border-top-1 ${
          status === "Completed" ? "border-primary" : "border-gold"
        }`}
      />
      <article className="border-x border-bottom border-base-lighter padding-2 padding-top-0">
        {status === "Completed" ? (
          <CompletedStatusCard {...props} />
        ) : (
          <InProgressStatusCard {...props} />
        )}
      </article>
    </div>
  );
};

export default ApplicationCard;
