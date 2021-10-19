// @ts-nocheck https://lwd.atlassian.net/browse/PORTAL-427
import routeWithParams, {
  createRouteWithQuery,
} from "../utils/routeWithParams";

import BenefitsApplication from "../models/BenefitsApplication";
import BenefitsApplicationDocument from "../models/BenefitsApplicationDocument";
import ButtonLink from "./ButtonLink";
import Heading from "./Heading";
import LeaveReason from "../models/LeaveReason";
import LegalNoticeList from "./LegalNoticeList";
import React from "react";
import Spinner from "./Spinner";
import Tag from "./Tag";
import ThrottledButton from "./ThrottledButton";
import findKeyByValue from "../utils/findKeyByValue";
import getLegalNotices from "../utils/getLegalNotices";
import hasDocumentsLoadError from "../utils/hasDocumentsLoadError";
import { useTranslation } from "../locales/i18n";
import withClaimDocuments from "../hoc/withClaimDocuments";

/**
 * Assists with page navigation, displays errors on the
 * current page rather than redirecting and showing the
 * error on a new page.
 */
const navigateToPage = async (claim, appLogic, href) => {
  const { fineos_absence_id } = claim;
  const claimDetail = await appLogic.claims.loadClaimDetail(fineos_absence_id);
  const isValidClaim = claimDetail?.fineos_absence_id === fineos_absence_id;

  // navigate to page if claim loads w/o errors
  if (isValidClaim) appLogic.portalFlow.goTo(href);
};

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
  appLogic: {
    claims: {
      isLoadingClaimDetail?: boolean;
      loadClaimDetail: (...args: any[]) => any;
    };
    portalFlow: {
      goTo: (...args: any[]) => any;
    };
  };
  claim: BenefitsApplication;
}

/**
 * Section to view notices and upload documents
 */
const ManageDocumentSection = ({
  appLogic,
  claim,
}: ManageDocumentSectionProps) => {
  const { t } = useTranslation();
  const { fineos_absence_id: absence_case_id } = claim;

  const onClickHandler = async (href) => {
    await navigateToPage(claim, appLogic, href);
  };

  const viewNoticesLink = createRouteWithQuery(
    "/applications/status/",
    { absence_case_id },
    "view_notices"
  );

  const uploadDocumentsLink = createRouteWithQuery(
    "/applications/status/",
    { absence_case_id },
    "upload_documents"
  );

  return (
    <div className="border-top border-base-lighter">
      <Heading className="padding-y-3" level="4">
        {t("components.applicationCardV2.otherActions")}
      </Heading>
      <ThrottledButton
        className="display-block margin-bottom-3"
        onClick={() => onClickHandler(viewNoticesLink)}
        variation="unstyled"
      >
        {t("components.applicationCardV2.viewNotices")}
      </ThrottledButton>

      <ThrottledButton
        className="display-block margin-bottom-2"
        onClick={() => onClickHandler(uploadDocumentsLink)}
        variation="unstyled"
      >
        {t("components.applicationCardV2.respondToRequest")}
      </ThrottledButton>
    </div>
  );
};

interface LegalNoticeSectionProps {
  appLogic: {
    appErrors: any;
    documents?: {
      download: (...args: any[]) => any;
    };
  };
  claim: BenefitsApplication;
  documents?: BenefitsApplicationDocument[];
  isLoadingDocuments: boolean;
}

/**
 * Section to view legal notices for in-progress applications
 */
const LegalNoticeSection = (props: LegalNoticeSectionProps) => {
  const { t } = useTranslation();
  const isSubmitted = props.claim.status === "Submitted";
  const legalNotices = getLegalNotices(props.documents);
  const shouldShowSpinner =
    props.isLoadingDocuments &&
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
          aria-valuetext={t("components.applicationCardV2.loadingLabel")}
        />
      </div>
    );
  }

  if (!legalNotices.length) return null;

  return (
    <div className="margin-top-2 padding-bottom-1" style={{ maxWidth: 385 }}>
      <Heading level="3">
        {t("components.applicationCardV2.viewNotices")}
      </Heading>
      <LegalNoticeList
        onDownloadClick={props.appLogic.documents.download}
        {...props}
      />
    </div>
  );
};

interface InProgressStatusCardProps {
  claim: BenefitsApplication;
  isLoadingDocuments: boolean;
  number: number;
  appLogic: any;
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
        title={t("components.applicationCardV2.heading", {
          number,
        })}
      />
      <Tag
        className="text-no-wrap"
        state="warning"
        label={t("components.applicationCardV2.inProgressTag")}
      />
      <p>{t("components.applicationCardV2.inProgressText")}</p>
      {claim.employer_fein && (
        <TitleAndDetailSectionItem
          title={t("components.applicationCardV2.employerEIN")}
          details={claim.employer_fein}
        />
      )}
      <LegalNoticeSection {...props} />
      <div className="border-top border-base-lighter padding-top-2">
        <ButtonLink
          className="display-flex flex-align-center flex-justify-center flex-column margin-right-0"
          href={routeWithParams("applications.checklist", {
            claim_id: claim.application_id,
          })}
        >
          <div>{t("components.applicationCardV2.continueApplication")}</div>
        </ButtonLink>
      </div>
    </React.Fragment>
  );
};

interface CompletedStatusCardProps {
  claim: BenefitsApplication;
  appLogic: {
    claims: {
      isLoadingClaimDetail?: boolean;
      loadClaimDetail: (...args: any[]) => any;
    };
    portalFlow: {
      goTo: (...args: any[]) => any;
    };
  };
}

/**
 * Status card for claim.status = "Completed"
 */
const CompletedStatusCard = ({ appLogic, claim }: CompletedStatusCardProps) => {
  const { t } = useTranslation();

  const leaveReasonText = t("components.applicationCardV2.leaveReasonValue", {
    context: findKeyByValue(LeaveReason, claim.leave_details?.reason),
  });

  const statusPage = routeWithParams("applications.status", {
    absence_case_id: claim.fineos_absence_id,
  });

  const onClickHandler = async () => {
    await navigateToPage(claim, appLogic, statusPage);
  };

  return (
    <React.Fragment>
      <HeaderSection title={leaveReasonText} />
      <TitleAndDetailSectionItem
        title={t("components.applicationCardV2.applicationID")}
        details={claim.fineos_absence_id}
      />
      <TitleAndDetailSectionItem
        title={t("components.applicationCardV2.employerEIN")}
        details={claim.employer_fein}
      />

      <div className="border-top border-base-lighter padding-y-2 margin-y-2 margin-bottom-0">
        <ThrottledButton
          className="width-full display-flex flex-align-center flex-justify-center flex-column margin-right-0"
          onClick={onClickHandler}
        >
          {t("components.applicationCardV2.viewStatusUpdatesAndDetails")}
        </ThrottledButton>
      </div>
      <ManageDocumentSection appLogic={appLogic} claim={claim} />
    </React.Fragment>
  );
};

interface ApplicationCardV2Props {
  claim: BenefitsApplication;
  appLogic: {
    appErrors: any;
    claims: {
      isLoadingClaimDetail?: boolean;
      loadClaimDetail: (...args: any[]) => any;
    };
    documents?: {
      download: (...args: any[]) => any;
    };
    portalFlow: {
      goTo: (...args: any[]) => any;
    };
  };
  isLoadingDocuments: boolean;
  number: number;
}

/**
 * Main entry point for an existing benefits Application, allowing
 * claimants to continue an in progress application, view what
 * they've submitted, view notices and instructions, or upload
 * additional docs.
 */
export const ApplicationCardV2 = (props: ApplicationCardV2Props) => {
  const {
    claim: { status },
  } = props;

  return (
    <div className="maxw-mobile-lg margin-bottom-3">
      <aside
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

export default withClaimDocuments(ApplicationCardV2);
