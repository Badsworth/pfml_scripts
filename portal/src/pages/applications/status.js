import ClaimDetail, { AbsencePeriod } from "../../models/ClaimDetail";
import React, { useEffect } from "react";
import { find, get, has, map } from "lodash";
import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import DocumentCollection from "../../models/DocumentCollection";
import { DocumentType } from "../../models/Document";
import Heading from "../../components/Heading";
import LeaveReason from "../../models/LeaveReason";
import LegalNoticeList from "../../components/LegalNoticeList.js";
import PropTypes from "prop-types";
import Spinner from "../../components/Spinner";
import Tag from "../../components/Tag";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import findDocumentsByTypes from "../../utils/findDocumentsByTypes";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDate from "../../utils/formatDate";
import getLegalNotices from "../../utils/getLegalNotices";
import hasDocumentsLoadError from "../../utils/hasDocumentsLoadError";
import { isFeatureEnabled } from "../../services/featureFlags";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

const nextStepsRoute = {
  newborn: "applications.upload.bondingProofOfBirth",
  adoption: "applications.upload.bondingProofOfPlacement",
};

export const Status = ({ appLogic, query }) => {
  const { t } = useTranslation();
  const {
    claims: { claimDetail, isLoadingClaimDetail, loadClaimDetail },
    documents: {
      documents: allClaimDocuments,
      download: downloadDocument,
      hasLoadedClaimDocuments,
      loadAll: loadAllClaimDocuments,
    },
    portalFlow,
  } = appLogic;
  const { absence_case_id } = query;

  useEffect(() => {
    if (!isFeatureEnabled("claimantShowStatusPage")) {
      portalFlow.goTo(routes.applications.index);
    }
  }, [portalFlow]);

  useEffect(() => {
    loadClaimDetail(absence_case_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [absence_case_id]);

  useEffect(() => {
    const application_id = get(claimDetail, "application_id");
    if (application_id) {
      loadAllClaimDocuments(application_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claimDetail]);

  useEffect(() => {
    /**
     * If URL includes a location.hash then page
     * should scroll into view on that id tag,
     * provided the id tag exists.
     */
    if (location.hash) {
      const anchorId = document.getElementById(location.hash.substring(1));
      if (anchorId) anchorId.scrollIntoView();
    }
  }, [isLoadingClaimDetail, claimDetail]);

  const hasClaimDetailLoadError = appLogic.appErrors.items.some(
    (error) => error.name === "ClaimDetailLoadError"
  );

  if (hasClaimDetailLoadError) return null;

  // Check both because claimDetail could be cached from a different status page.
  if (isLoadingClaimDetail || !claimDetail)
    return (
      <div className="margin-top-8 text-center">
        <Spinner
          aria-valuetext={t("pages.claimsStatus.loadingClaimDetailLabel")}
        />
      </div>
    );

  const absenceDetails = claimDetail.absencePeriodsByReason;
  const hasPendingStatus = claimDetail.absence_periods.some(
    (absenceItem) => absenceItem.request_decision === "Pending"
  );
  const documentsForApplication = allClaimDocuments.filterByApplication(
    claimDetail.application_id
  );

  const ViewYourNotices = () => {
    const legalNotices = getLegalNotices(documentsForApplication);

    const shouldShowSpinner =
      !hasLoadedClaimDocuments(claimDetail.application_id) &&
      !hasDocumentsLoadError(appLogic.appErrors, claimDetail.application_id);
    const hasNothingToShow =
      hasDocumentsLoadError(appLogic.appErrors, claimDetail.application_id) ||
      legalNotices.length === 0;

    const SectionWrapper = ({ children }) => (
      <div
        className="border-top border-base-lighter padding-y-2"
        id="view_notices"
      >
        {children}
      </div>
    );

    SectionWrapper.propTypes = {
      children: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.node),
        PropTypes.node,
      ]).isRequired,
    };

    if (shouldShowSpinner) {
      // claim documents are loading.
      return (
        <SectionWrapper>
          <Spinner
            aria-valuetext={t("pages.claimsStatus.loadingLegalNoticesLabel")}
          />
        </SectionWrapper>
      );
    }

    const sectionBody = hasNothingToShow ? (
      <p>{t("pages.claimsStatus.legalNoticesFallback")}</p>
    ) : (
      <LegalNoticeList
        documents={legalNotices}
        onDownloadClick={downloadDocument}
      />
    );

    return (
      <SectionWrapper>
        <Heading className="margin-bottom-1" level="2" id="view_notices">
          {t("pages.claimsStatus.viewNoticesHeading")}
        </Heading>
        {sectionBody}
      </SectionWrapper>
    );
  };

  const getInfoAlertContext = (absenceDetails) => {
    const hasBondingReason = has(absenceDetails, LeaveReason.bonding);
    const hasPregnancyReason = has(absenceDetails, LeaveReason.pregnancy);

    if (hasBondingReason && !hasPregnancyReason) {
      return "bonding";
    }

    if (hasPregnancyReason && !hasBondingReason) {
      return "pregnancy";
    }

    return "";
  };
  const infoAlertContext = getInfoAlertContext(absenceDetails);
  const [firstAbsenceDetail] = Object.keys(absenceDetails);
  const containerClassName = "border-top border-base-lighter padding-top-2";

  return (
    <React.Fragment>
      {!!infoAlertContext && (
        <Alert
          className="margin-bottom-3"
          data-test="info-alert"
          heading={t("pages.claimsStatus.infoAlertHeading", {
            context: infoAlertContext,
          })}
          headingLevel="2"
          headingSize="4"
          noIcon
          state="info"
        >
          <Trans
            i18nKey="pages.claimsStatus.infoAlertBody"
            tOptions={{ context: infoAlertContext }}
            components={{
              "about-bonding-leave-link": (
                <a
                  href={routes.external.massgov.benefitsGuide_aboutBondingLeave}
                  target="_blank"
                  rel="noreferrer noopener"
                />
              ),
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
        </Alert>
      )}
      <BackButton
        label={t("pages.claimsStatus.backButtonLabel")}
        href={routes.applications.index}
      />
      <div className="measure-6">
        <Title weight="normal" small>
          {t("pages.claimsStatus.applicationDetails")}
        </Title>

        {/* Heading section */}

        <Heading level="2" size="1">
          {t("pages.claimsStatus.leaveReasonValueHeader", {
            context: findKeyByValue(LeaveReason, firstAbsenceDetail),
          })}
        </Heading>
        <div className="display-flex border-base-lighter margin-bottom-3 bg-base-lightest padding-2">
          <div className="padding-right-10">
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.applicationID")}
            </Heading>
            <p className="text-bold">{absence_case_id}</p>
          </div>
          <div>
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.employerEIN")}
            </Heading>
            <p className="text-bold">{claimDetail.employer.employer_fein}</p>
          </div>
        </div>
        {hasPendingStatus && (
          <Timeline
            absencePeriods={claimDetail.absence_periods}
            employerFollowUpDate={
              claimDetail.managed_requirements[0]?.follow_up_date
            }
            absenceDetails={absenceDetails}
            applicationId={claimDetail.application_id}
            docList={documentsForApplication}
          />
        )}
        <LeaveDetails absenceDetails={absenceDetails} />
        <ViewYourNotices />

        {/* Upload documents section */}
        <div className={containerClassName} id="upload_documents">
          <Heading level="2">
            {t("pages.claimsStatus.uploadDocumentsHeading")}
          </Heading>
          <Heading level="3">
            {t("pages.claimsStatus.infoRequestsHeading")}
          </Heading>
          <p>{t("pages.claimsStatus.infoRequestsBody")}</p>
          <ButtonLink
            className="measure-6 margin-bottom-3"
            href={routeWithParams("applications.upload.index", {
              absence_case_id: claimDetail.fineos_absence_id,
            })}
          >
            {t("pages.claimsStatus.uploadDocumentsButton")}
          </ButtonLink>
        </div>

        {/* Manage applications section */}
        <div className={containerClassName}>
          <Heading level="2">
            {t("pages.claimsStatus.manageApplicationHeading")}
          </Heading>
          <Heading level="3">
            {t("pages.claimsStatus.makeChangesHeading")}
          </Heading>
          <Trans
            i18nKey="pages.claimsStatus.makeChangesBody"
            components={{
              "contact-center-phone-link": (
                <a
                  href={`tel:${t("shared.contactCenterPhoneNumberNoBreak")}`}
                />
              ),
            }}
          />
          <Heading level="3">
            {t("pages.claimsStatus.reportOtherBenefitsHeading")}
          </Heading>
          <Trans
            i18nKey="pages.claimsStatus.reportOtherBenefitsBody"
            components={{
              "contact-center-phone-link": (
                <a
                  href={`tel:${t("shared.contactCenterPhoneNumberNoBreak")}`}
                />
              ),
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
          />
        </div>
      </div>
    </React.Fragment>
  );
};

Status.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    claims: PropTypes.shape({
      claimDetail: PropTypes.instanceOf(ClaimDetail),
      isLoadingClaimDetail: PropTypes.bool,
      loadClaimDetail: PropTypes.func.isRequired,
    }).isRequired,
    documents: PropTypes.shape({
      documents: PropTypes.instanceOf(DocumentCollection).isRequired,
      download: PropTypes.func.isRequired,
      hasLoadedClaimDocuments: PropTypes.func.isRequired,
      loadAll: PropTypes.func.isRequired,
    }),
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    absence_case_id: PropTypes.string,
  }).isRequired,
};

export default Status;

export const StatusTagMap = {
  Approved: "success",
  Denied: "error",
  Pending: "pending",
  Withdrawn: "inactive",
};

export const LeaveDetails = ({ absenceDetails = {} }) => {
  const { t } = useTranslation();
  return map(absenceDetails, (absenceItem, absenceItemName) => (
    <div key={absenceItemName} className="border-base-lighter margin-bottom-2">
      <Heading level="2">
        {t("pages.claimsStatus.leaveReasonValue", {
          context: findKeyByValue(LeaveReason, absenceItemName),
        })}
      </Heading>
      {absenceItem.length
        ? absenceItem.map(
            ({
              period_type,
              absence_period_start_date,
              absence_period_end_date,
              request_decision,
              fineos_leave_request_id,
            }) => (
              <div key={fineos_leave_request_id} className="margin-top-2">
                <Heading className="margin-bottom-1" level="3">
                  {t("pages.claimsStatus.leavePeriodLabel", {
                    context: period_type.split(" ")[0].toLowerCase(),
                  })}
                </Heading>
                <p>
                  {`From ${formatDate(
                    absence_period_start_date
                  ).full()} to ${formatDate(absence_period_end_date).full()}`}
                </p>
                <Tag
                  paddingSm
                  label={request_decision}
                  state={StatusTagMap[request_decision]}
                />
                <Trans
                  i18nKey="pages.claimsStatus.leaveStatusMessage"
                  tOptions={{ context: request_decision }}
                  components={{
                    "application-link": (
                      <a href={routes.applications.getReady} />
                    ),
                    "notice-link": <a href="#view_notices" />,
                    "request-appeal-link": (
                      <a
                        href={routes.external.massgov.requestAnAppealForPFML}
                      />
                    ),
                  }}
                />
              </div>
            )
          )
        : null}
    </div>
  ));
};

LeaveDetails.propTypes = {
  absenceDetails: PropTypes.object,
};

export const Timeline = ({
  employerFollowUpDate = null,
  applicationId,
  docList,
  absencePeriods,
}) => {
  const { t } = useTranslation();

  const shouldRenderCertificationButton = (absencePeriodReason, docList) =>
    !findDocumentsByTypes(docList, [
      DocumentType.certification[absencePeriodReason],
    ]).length;

  const bondingAbsencePeriod = find(
    absencePeriods,
    (absencePeriod) =>
      absencePeriod.reason === LeaveReason.pregnancy ||
      absencePeriod.reason === LeaveReason.bonding
  );

  // eslint-disable-next-line react/prop-types
  const FollowUpSteps = ({ bondingAbsencePeriod }) => {
    const typeOfProof = ["Foster Care", "Adoption"].includes(
      // eslint-disable-next-line react/prop-types
      bondingAbsencePeriod.reason_qualifier_one
    )
      ? "adoption"
      : "newborn";

    return (
      <React.Fragment>
        <Heading level="2">{t("pages.claimsStatus.whatYouNeedToDo")}</Heading>
        <p>
          {t("pages.claimsStatus.whatYouNeedToDoText", {
            context: typeOfProof,
          })}
        </p>
        <ButtonLink
          className="measure-12"
          href={routeWithParams(nextStepsRoute[typeOfProof], {
            claim_id: applicationId,
          })}
        >
          {t("pages.claimsStatus.whatHappensNextButton", {
            context: typeOfProof,
          })}
        </ButtonLink>
      </React.Fragment>
    );
  };

  const ApplicationTimeline = () => (
    <React.Fragment>
      <Heading level="2">{t("pages.claimsStatus.timelineHeading")}</Heading>
      <Trans
        i18nKey="pages.claimsStatus.timelineDescription"
        components={{
          ul: <ul className="usa-list" />,
          li: <li />,
        }}
      />
      <Trans
        i18nKey={
          employerFollowUpDate
            ? "pages.claimsStatus.timelineTextFollowUpEmployer"
            : "pages.claimsStatus.timelineTextFollowUpGenericEmployer"
        }
        tOptions={{
          employerFollowUpDate: formatDate(employerFollowUpDate).short(),
        }}
      />
      <Trans i18nKey="pages.claimsStatus.timelineTextFollowUpGenericDFML" />
      <Trans
        i18nKey="pages.claimsStatus.timelineTextLearnMore"
        components={{
          "timeline-link": <a href={routes.external.massgov.timeline} />,
        }}
      />
    </React.Fragment>
  );
  return (
    <div className="border-bottom border-base-lighter padding-bottom-2 margin-bottom-2">
      {!bondingAbsencePeriod ||
      // eslint-disable-next-line react/prop-types
      !shouldRenderCertificationButton(bondingAbsencePeriod.reason, docList) ? (
        <ApplicationTimeline />
      ) : (
        <FollowUpSteps bondingAbsencePeriod={bondingAbsencePeriod} />
      )}
    </div>
  );
};

Timeline.propTypes = {
  absencePeriods: PropTypes.arrayOf(PropTypes.instanceOf(AbsencePeriod))
    .isRequired,
  applicationId: PropTypes.string,
  employerFollowUpDate: PropTypes.string,
  docList: PropTypes.array.isRequired,
};
