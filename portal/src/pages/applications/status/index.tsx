import {
  BenefitsApplicationDocument,
  ClaimDocument,
  DocumentType,
  DocumentTypeEnum,
  filterByApplication,
  findDocumentsByTypes,
  getLegalNotices,
} from "../../../models/Document";
import React, { useEffect } from "react";
import {
  getInfoAlertContext,
  paymentStatusViewHelper,
  showPaymentsTab,
} from "./payments";
import withUser, { WithUserProps } from "../../../hoc/withUser";

import { AbsencePeriod } from "../../../models/AbsencePeriod";
import AbsencePeriodStatusTag from "../../../components/AbsencePeriodStatusTag";
import Alert from "../../../components/core/Alert";
import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
import ButtonLink from "../../../components/ButtonLink";
import Heading from "../../../components/core/Heading";
import LeaveReason from "../../../models/LeaveReason";
import LegalNoticeList from "../../../components/LegalNoticeList";
import PageNotFound from "../../../components/PageNotFound";
import { Payment } from "src/models/Payment";
import Spinner from "../../../components/core/Spinner";
import StatusNavigationTabs from "../../../components/status/StatusNavigationTabs";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { createRouteWithQuery } from "../../../utils/routeWithParams";
import findKeyByValue from "../../../utils/findKeyByValue";
import formatDate from "../../../utils/formatDate";
import hasDocumentsLoadError from "../../../utils/hasDocumentsLoadError";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

const containerClassName = "border-bottom border-base-lighter padding-y-4";

export const Status = ({
  appLogic,
  query,
}: WithUserProps & {
  query: {
    absence_case_id?: string;
    absence_id?: string;
    uploaded_document_type?: string;
  };
}) => {
  const { t } = useTranslation();
  const {
    claims: { claimDetail, loadClaimDetail, isLoadingClaimDetail },
    documents: {
      documents: allClaimDocuments,
      download: downloadDocument,
      hasLoadedClaimDocuments,
      loadAll: loadAllClaimDocuments,
    },
    payments: { loadPayments, loadedPaymentsData },
  } = appLogic;
  const { absence_case_id, absence_id, uploaded_document_type } = query;
  const application_id = claimDetail?.application_id;
  const absenceId = absence_id || absence_case_id;
  const hasDocuments = hasLoadedClaimDocuments(
    claimDetail?.application_id || ""
  );
  const hasDocumentsError = hasDocumentsLoadError(
    appLogic.errors,
    claimDetail?.application_id || ""
  );

  useEffect(() => {
    if (absenceId) {
      loadClaimDetail(absenceId);
      loadPayments(absenceId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [absenceId]);

  useEffect(() => {
    if (application_id) {
      loadAllClaimDocuments(application_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [application_id]);

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
  }, [hasDocuments, hasDocumentsError, isLoadingClaimDetail]);

  /**
   * If there is no absence_id query parameter,
   * then return the PFML 404 page.
   */
  const isAbsenceCaseId = Boolean(absenceId?.length);
  if (!isAbsenceCaseId) return <PageNotFound />;

  // only hide page content if there is an error that's not DocumentsLoadError.
  const hasNonDocumentsLoadError: boolean = appLogic.errors.some(
    (error) => error.name !== "DocumentsLoadError"
  );
  if (hasNonDocumentsLoadError) {
    return (
      <BackButton
        label={t("pages.claimsStatus.backButtonLabel")}
        href={routes.applications.index}
      />
    );
  }

  // Check both because claimDetail could be cached from a different status page.
  if (isLoadingClaimDetail || !claimDetail) {
    return (
      <div className="text-center">
        <Spinner aria-label={t("pages.claimsStatus.loadingClaimDetailLabel")} />
      </div>
    );
  }

  const absenceDetails = AbsencePeriod.groupByReason(
    claimDetail.absence_periods
  );

  const documentsForApplication = filterByApplication(
    allClaimDocuments.items,
    claimDetail.application_id
  );

  const helper = paymentStatusViewHelper(
    claimDetail,
    allClaimDocuments,
    loadedPaymentsData || new Payment()
  );

  const {
    hasApprovedStatus,
    hasPendingStatus,
    hasInReviewStatus,
    hasProjectedStatus,
  } = helper;

  const infoAlertContext = getInfoAlertContext(helper);

  const viewYourNotices = () => {
    const legalNotices = getLegalNotices(documentsForApplication);
    const hasNothingToShow = hasDocumentsError || legalNotices.length === 0;
    interface SectionWrapperProps {
      children: React.ReactNode;
    }
    const SectionWrapper = ({ children }: SectionWrapperProps) => (
      <div className={containerClassName}>{children}</div>
    );

    if (!hasDocuments && !hasDocumentsError) {
      return (
        <SectionWrapper>
          <Spinner
            aria-label={t("pages.claimsStatus.loadingLegalNoticesLabel")}
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

    // How many claim decisions
    const expectedNoticeCount = claimDetail.absence_periods.reduce(
      (previousValue, { request_decision }) => {
        const shouldHaveNotice =
          request_decision === "Approved" ||
          request_decision === "Denied" ||
          request_decision === "Withdrawn";

        if (shouldHaveNotice) return previousValue + 1;
        return previousValue;
      },
      0
    );

    // Legal notices which match notice types above
    const noticeTypes: DocumentTypeEnum[] = [
      DocumentType.approvalNotice,
      DocumentType.denialNotice,
      DocumentType.withdrawalNotice,
    ];

    const decisionNotices = legalNotices.filter((legalNotice) => {
      return noticeTypes.includes(legalNotice.document_type);
    });

    // Show timeline for notice if there are no notices and expectedNotices > amount of Notices
    const isStatusTimelineNotice = !decisionNotices.length
      ? expectedNoticeCount > decisionNotices.length
      : null;

    return (
      <SectionWrapper>
        <Heading level="2" id="view_notices">
          {t("pages.claimsStatus.viewNoticesHeading")}
        </Heading>
        {sectionBody}
        {isStatusTimelineNotice && (
          <p className="text-light">
            {t("pages.claimsStatus.statusTimelineNotice")}
          </p>
        )}
      </SectionWrapper>
    );
  };

  const [firstAbsenceDetail] = Object.keys(absenceDetails);

  // Determines if payment tab is displayed
  const isPaymentsTab = showPaymentsTab(helper);

  return (
    <React.Fragment>
      {uploaded_document_type && (
        <Alert
          heading={t("pages.claimsStatus.uploadSuccessHeading", {
            document: t("pages.claimsStatus.uploadSuccessHeadingDocumentName", {
              context: uploaded_document_type,
            }),
          })}
          state="success"
        >
          {t("pages.applications.uploadSuccessMessage", {
            absence_id: absenceId,
          })}
        </Alert>
      )}

      {!!infoAlertContext &&
        (hasPendingStatus ||
          hasApprovedStatus ||
          hasInReviewStatus ||
          hasProjectedStatus) && (
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
            <p>
              <Trans
                i18nKey="pages.claimsStatus.infoAlertBody"
                tOptions={{ context: infoAlertContext }}
                components={{
                  "about-bonding-leave-link": (
                    <a
                      href={
                        routes.external.massgov.benefitsGuide_aboutBondingLeave
                      }
                      target="_blank"
                      rel="noreferrer noopener"
                    />
                  ),
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                }}
              />
            </p>
          </Alert>
        )}
      <BackButton
        label={t("pages.claimsStatus.backButtonLabel")}
        href={routes.applications.index}
      />
      <div className="measure-6">
        <Title hidden>{t("pages.claimsStatus.applicationTitle")}</Title>
        {isPaymentsTab && (
          <StatusNavigationTabs
            activePath={appLogic.portalFlow.pathname}
            absence_id={absenceId}
          />
        )}

        {/* Heading section */}
        <Heading level="2" size="1">
          {t("pages.claimsStatus.leaveReasonValueHeader", {
            context: findKeyByValue(LeaveReason, firstAbsenceDetail),
          })}
        </Heading>

        <div className="bg-base-lightest tablet:display-flex padding-3">
          <div className=" padding-right-6">
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.applicationID")}
            </Heading>
            <p className="text-bold">{absenceId}</p>
          </div>
          {claimDetail.employer && (
            <div>
              <Heading weight="normal" level="2" size="4">
                {t("pages.claimsStatus.employerEIN")}
              </Heading>
              <p className="text-bold">{claimDetail.employer.employer_fein}</p>
            </div>
          )}
        </div>

        {hasPendingStatus && (
          <Timeline
            absencePeriods={claimDetail.absence_periods}
            employerFollowUpDate={
              claimDetail.managedRequirementByFollowUpDate[0]?.follow_up_date
            }
            applicationId={claimDetail.application_id}
            docList={documentsForApplication}
            absenceId={claimDetail.fineos_absence_id}
            appLogic={appLogic}
          />
        )}
        <LeaveDetails
          absenceDetails={absenceDetails}
          absenceId={claimDetail.fineos_absence_id}
          isPaymentsTab={isPaymentsTab}
        />
        {viewYourNotices()}

        {/* Upload documents section */}
        <div className={containerClassName} id="upload_documents">
          <Heading level="2">
            {t("pages.claimsStatus.infoRequestsHeading")}
          </Heading>
          <div>
            <Trans
              i18nKey="pages.claimsStatus.infoRequestsBody"
              tOptions={{ context: !hasPendingStatus ? "Decision" : "Pending" }}
              components={{
                "online-appeals-form": (
                  <a
                    href={routes.external.massgov.onlineAppealsForm}
                    target="_blank"
                    rel="noreferrer noopener"
                  />
                ),
                p: <p className="margin-top-1"></p>,
              }}
            />
          </div>
          {hasPendingStatus && (
            <ButtonLink
              className="margin-top-3"
              href={appLogic.portalFlow.getNextPageRoute(
                "UPLOAD_DOC_OPTIONS",
                {},
                { absence_id: claimDetail.fineos_absence_id }
              )}
            >
              {t("pages.claimsStatus.uploadDocumentsButton")}
            </ButtonLink>
          )}
        </div>

        {/* Manage applications section */}
        {(hasPendingStatus || hasApprovedStatus) && (
          <div className="padding-y-4" data-testid="manageApplication">
            <div>
              <Heading level="2">
                {t("pages.claimsStatus.manageApplicationHeading")}
              </Heading>
              <Heading level="3" className="margin-top-3">
                {t("pages.claimsStatus.makeChangesHeading")}
              </Heading>
              <Trans
                i18nKey="pages.claimsStatus.makeChangesBody"
                components={{
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                }}
              />
              {hasApprovedStatus && (
                <Trans
                  i18nKey="pages.claimsStatus.manageApprovedApplicationText"
                  components={{
                    "manage-approved-app-link": (
                      <a
                        data-testid="manageApprovedApplicationLink"
                        href={routes.external.massgov.manageApprovedApplication}
                        rel="noopener noreferrer"
                        target="_blank"
                      />
                    ),
                  }}
                />
              )}
            </div>

            <Heading level="3">
              {t("pages.claimsStatus.reportOtherBenefitsHeading")}
            </Heading>
            <Trans
              i18nKey="pages.claimsStatus.reportOtherBenefitsBody"
              components={{
                "contact-center-phone-link": (
                  <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                ),
                ul: <ul className="usa-list" />,
                li: <li />,
              }}
            />
          </div>
        )}
      </div>
    </React.Fragment>
  );
};

export default withUser(Status);

interface LeaveDetailsProps {
  absenceDetails?: { [key: string]: AbsencePeriod[] };
  absenceId: string;
  isPaymentsTab?: boolean;
}

export const LeaveDetails = ({
  absenceDetails = {},
  absenceId,
  isPaymentsTab,
}: LeaveDetailsProps) => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      {Object.entries(absenceDetails).map(([absenceItemName, absenceItem]) => (
        <div key={absenceItemName} className={containerClassName}>
          <Heading level="2">
            {t("pages.claimsStatus.leaveReasonValue", {
              context: findKeyByValue(LeaveReason, absenceItemName),
            })}
          </Heading>
          {absenceItem.length &&
            absenceItem.map(
              (
                {
                  period_type,
                  absence_period_start_date,
                  absence_period_end_date,
                  request_decision,
                  fineos_leave_request_id,
                },
                ind
              ) => (
                <div
                  key={fineos_leave_request_id}
                  className={`margin-top-${ind ? "6" : "4"}`}
                >
                  <Heading level="3">
                    {t("pages.claimsStatus.leavePeriodLabel", {
                      context: period_type.split(" ")[0].toLowerCase(),
                    })}
                  </Heading>
                  <p>
                    {t("pages.claimsStatus.leavePeriodDates", {
                      endDate: formatDate(absence_period_end_date).full(),
                      startDate: formatDate(absence_period_start_date).full(),
                    })}
                  </p>
                  <p>
                    <AbsencePeriodStatusTag
                      request_decision={request_decision}
                    />
                  </p>
                  <div data-testid="leaveStatusMessage">
                    <Trans
                      i18nKey="pages.claimsStatus.leaveStatusMessage"
                      tOptions={{ context: request_decision }}
                      components={{
                        "application-link": (
                          <a href={routes.applications.getReady} />
                        ),
                        "request-appeal-link": (
                          <a
                            href={
                              routes.external.massgov.requestAnAppealForPFML
                            }
                            rel="noopener noreferrer"
                            target="_blank"
                          />
                        ),
                      }}
                    />
                  </div>

                  {request_decision === "Approved" && isPaymentsTab && (
                    <Trans
                      i18nKey="pages.claimsStatus.viewPaymentTimeline"
                      components={{
                        "payments-page-link": (
                          <a
                            href={createRouteWithQuery(
                              "/applications/status/payments",
                              { absence_id: absenceId }
                            )}
                          />
                        ),
                      }}
                    />
                  )}
                </div>
              )
            )}
        </div>
      ))}
    </React.Fragment>
  );
};

interface TimelineProps {
  absencePeriods: AbsencePeriod[];
  applicationId?: string;
  employerFollowUpDate: string | null;
  docList: ClaimDocument[] | BenefitsApplicationDocument[];
  absenceId: string;
  appLogic: AppLogic;
}

export const Timeline = ({
  employerFollowUpDate = null,
  applicationId,
  docList,
  absencePeriods,
  absenceId,
  appLogic,
}: TimelineProps) => {
  const { t } = useTranslation();

  const shouldRenderCertificationButton = (
    absencePeriodReason: keyof typeof DocumentType.certification,
    docList: BenefitsApplicationDocument[] | ClaimDocument[]
  ) =>
    !findDocumentsByTypes(docList, [
      DocumentType.certification[absencePeriodReason],
    ]).length;

  const bondingAbsencePeriod = absencePeriods.find(
    (absencePeriod) => absencePeriod.reason === LeaveReason.bonding
  );
  interface FollowUpStepsProps {
    bondingAbsencePeriod: AbsencePeriod;
  }
  const FollowUpSteps = ({ bondingAbsencePeriod }: FollowUpStepsProps) => {
    let typeOfProof;
    if (bondingAbsencePeriod.reason_qualifier_one === "Adoption") {
      typeOfProof = "adoption";
    } else if (bondingAbsencePeriod.reason_qualifier_one === "Foster Care") {
      typeOfProof = "fosterCare";
    } else {
      typeOfProof = "newborn";
    }

    return (
      <React.Fragment>
        <Heading level="2">{t("pages.claimsStatus.whatYouNeedToDo")}</Heading>
        <p>
          <Trans
            i18nKey="pages.claimsStatus.whatYouNeedToDoText"
            tOptions={{ context: typeOfProof }}
            components={{
              "proof-document-link": (
                <a
                  href={routes.external.massgov.proofOfBirthOrPlacement}
                  rel="noopener noreferrer"
                  target="_blank"
                />
              ),
            }}
          />
        </p>
        <ButtonLink
          href={appLogic.portalFlow.getNextPageRoute(
            typeOfProof === "newborn"
              ? "UPLOAD_PROOF_OF_BIRTH"
              : "UPLOAD_PROOF_OF_PLACEMENT",
            {},
            { claim_id: applicationId, absence_id: absenceId }
          )}
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
        i18nKey="pages.claimsStatus.timelineDescription"
        components={{
          ul: <ul className="usa-list" />,
          li: <li />,
        }}
      />
      <Trans i18nKey="pages.claimsStatus.timelineTextFollowUpMayTakeLonger" />
      <Trans
        i18nKey="pages.claimsStatus.timelineTextLearnMore"
        components={{
          "timeline-link": (
            <a
              href={routes.external.massgov.timeline}
              rel="noopener noreferrer"
              target="_blank"
            />
          ),
        }}
      />
    </React.Fragment>
  );
  return (
    <div data-testid="timeline" className={containerClassName}>
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
