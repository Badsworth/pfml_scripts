import routeWithParams, {
  createRouteWithQuery,
} from "../utils/routeWithParams";

import BenefitsApplication from "../models/BenefitsApplication";
import ButtonLink from "../components/ButtonLink";
import Heading from "../components/Heading";
import Icon from "../components/Icon";
import LeaveReason from "../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import findKeyByValue from "../utils/findKeyByValue";
import { useTranslation } from "../locales/i18n";

/**
 * Main header for the top of status cards
 */
const HeaderSection = ({ title }) => (
  <Heading className="margin-bottom-1 padding-2 padding-top-3" level="2">
    {title}
  </Heading>
);

HeaderSection.propTypes = {
  title: PropTypes.string.isRequired,
};

/**
 * Group together details for status cards
 */
const TitleAndDetailSectionItem = ({ details, title }) => (
  <div className="padding-2 padding-bottom-1 padding-top-0 margin-top-0">
    <Heading level="4" size="6">
      {title}
    </Heading>
    <p className="margin-bottom-05 margin-top-05 text-bold">{details}</p>
  </div>
);

TitleAndDetailSectionItem.propTypes = {
  details: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
};

/**
 * Button section with top border and optional header text/section
 */
const ButtonSection = ({ buttonText, href, iconComponent = null }) => {
  return (
    <div className="border-top border-base-lighter padding-2 margin-1 margin-bottom-0">
      <ButtonLink
        className="display-flex flex-align-center flex-justify-center flex-column"
        href={href}
      >
        <div>{buttonText}</div>
        {iconComponent}
      </ButtonLink>
    </div>
  );
};

ButtonSection.propTypes = {
  buttonText: PropTypes.string.isRequired,
  href: PropTypes.string.isRequired,
  iconComponent: PropTypes.object,
};

ButtonSection.defaultProps = {
  iconComponent: null,
};

/**
 * Section to view notices and upload documents
 */
const ManageDocumentSection = ({ claim }) => {
  const { t } = useTranslation();
  const { fineos_absence_id: absence_case_id } = claim;

  const viewNoticesLink = createRouteWithQuery(
    "/applications/status/#view_notices",
    { absence_case_id }
  );

  const uploadDocumentsLink = createRouteWithQuery(
    "/applications/status/#upload_documents",
    { absence_case_id }
  );

  return (
    <div className="border-top border-base-lighter padding-2 padding-top-0 margin-1 margin-top-0">
      <Heading className="padding-bottom-3 padding-top-3" level="4">
        {t("components.applicationCardV2.manageApplicationDocuments")}
      </Heading>
      <ButtonLink
        className="display-block margin-bottom-3"
        href={viewNoticesLink}
        variation="unstyled"
      >
        {t("components.applicationCardV2.viewNotices")}
      </ButtonLink>

      <ButtonLink
        className="display-block margin-bottom-2"
        href={uploadDocumentsLink}
        variation="unstyled"
      >
        {t("components.applicationCardV2.uploadDocuments")}
      </ButtonLink>
    </div>
  );
};

ManageDocumentSection.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

/**
 * Status card for claim.status = "Completed"
 */
const CompletedStatusCard = ({ claim }) => {
  const { t } = useTranslation();

  const leaveReasonText = t("components.applicationCardV2.leaveReasonValue", {
    context: findKeyByValue(LeaveReason, claim.leave_details?.reason),
  });

  const iconComponent = (
    <Icon
      className="position-absolute flex-align-self-end margin-right-neg-105"
      fill="white"
      name="arrow_forward"
      size={3}
    />
  );

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

      <ButtonSection
        buttonText={t(
          "components.applicationCardV2.viewStatusUpdatesAndDetails"
        )}
        href={routeWithParams("applications.uploadDocsOptions", {
          claim_id: claim.application_id,
        })}
        iconComponent={iconComponent}
      />
      <ManageDocumentSection claim={claim} />
    </React.Fragment>
  );
};

CompletedStatusCard.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

/**
 * Status card for claim.status != "Completed" (In Progress)
 */
const InProgressStatusCard = ({ claim, number }) => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <HeaderSection
        title={t("components.applicationCardV2.heading", {
          number,
        })}
      />
      <TitleAndDetailSectionItem
        title={t("components.applicationCardV2.employerEIN")}
        details={claim.employer_fein}
      />
      <ButtonSection
        buttonText={t("components.applicationCardV2.continueApplication")}
        href={routeWithParams("applications.checklist", {
          claim_id: claim.application_id,
        })}
      />
    </React.Fragment>
  );
};

InProgressStatusCard.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  number: PropTypes.number.isRequired,
};

/**
 * Main entry point for an existing benefits Application, allowing
 * claimants to continue an in progress application, view what
 * they've submitted, view notices and instructions, or upload
 * additional docs.
 */
export const ApplicationCardV2 = (props) => {
  const {
    claim: { status },
  } = props;

  const StatusCard = () => {
    switch (status) {
      case "Completed":
        return <CompletedStatusCard {...props} />;

      default:
        return <InProgressStatusCard {...props} />;
    }
  };

  return (
    <React.Fragment>
      <aside className="maxw-mobile-lg border-top-1 border-primary" />
      <article className="maxw-mobile-lg border border-base-lighter border-top-0 margin-bottom-3">
        <StatusCard />
      </article>
    </React.Fragment>
  );
};

ApplicationCardV2.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default ApplicationCardV2;
