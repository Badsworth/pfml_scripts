import { DocumentType, DocumentTypeEnum } from "../../../models/Document";
import React, { useEffect } from "react";
import { find, get, has, map } from "lodash";
import { AbsencePeriod } from "../../../models/ClaimDetail";
import Alert from "../../../components/Alert";
import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
import BenefitsApplicationDocument from "../../../models/BenefitsApplicationDocument";
import ButtonLink from "../../../components/ButtonLink";
import ClaimDocument from "../../../models/ClaimDocument";
import Heading from "../../../components/Heading";
import LeaveReason from "../../../models/LeaveReason";
import LegalNoticeList from "../../../components/LegalNoticeList";
import PageNotFound from "../../../components/PageNotFound";
import Spinner from "../../../components/Spinner";
import StatusNavigationTabs from "../../../components/status/StatusNavigationTabs";
import Tag from "../../../components/Tag";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import findDocumentsByTypes from "../../../utils/findDocumentsByTypes";
import findKeyByValue from "../../../utils/findKeyByValue";
import formatDate from "../../../utils/formatDate";
import getLegalNotices from "../../../utils/getLegalNotices";
import hasDocumentsLoadError from "../../../utils/hasDocumentsLoadError";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

interface StatusProps {
  appLogic: AppLogic;
  query: {
    absence_case_id?: string;
    claim_id?: string;
    uploaded_document_type?: string;
  };
}

const containerClassName =
  "border-bottom border-base-lighter measure-6 padding-y-4";

export const Status = ({ appLogic, query }: StatusProps) => {
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
  const { absence_case_id, uploaded_document_type } = query;

  useEffect(() => {
    if (!isFeatureEnabled("claimantShowStatusPage")) {
      portalFlow.goTo(routes.applications.index);
    }
  }, [portalFlow]);

  useEffect(() => {
    if (absence_case_id) {
      loadClaimDetail(absence_case_id);
    }
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

  /**
   * If there is no absence_case_id query parameter,
   * then return the PFML 404 page.
   */
  const isAbsenceCaseId = Boolean(query.absence_case_id?.length);
  if (!isAbsenceCaseId) return <PageNotFound />;

  // only hide page content if there is an error that's not DocumentsLoadError.
  const hasNonDocumentsLoadError: boolean = appLogic.appErrors.items.some(
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
        <Spinner
          aria-valuetext={t("pages.claimsStatus.loadingClaimDetailLabel")}
        />
      </div>
    );
  }

  const absenceDetails = claimDetail.absencePeriodsByReason;
  const hasPendingStatus = claimDetail.absence_periods.some(
    (absenceItem) => absenceItem.request_decision === "Pending"
  );
  const hasApprovedStatus = claimDetail.absence_periods.some(
    (absenceItem) => absenceItem.request_decision === "Approved"
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

    interface SectionWrapperProps {
      children: React.ReactNode;
    }
    const SectionWrapper = ({ children }: SectionWrapperProps) => (
      <div className={containerClassName}>{children}</div>
    );

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

    // How many claim decisions
    const expectedNoticeCount = claimDetail.absence_periods.reduce(
      (acc, { request_decision }) => {
        const shouldHaveNotice =
          request_decision === "Approved" ||
          request_decision === "Denied" ||
          request_decision === "Withdrawn";

        if (shouldHaveNotice) acc += 1;
        return acc;
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

  const getInfoAlertContext = (
    absenceDetails: Record<string, AbsencePeriod[]>
  ) => {
    const hasBondingReason = has(absenceDetails, LeaveReason.bonding);
    const hasPregnancyReason = has(absenceDetails, LeaveReason.pregnancy);
    const hasNewBorn = claimDetail.absence_periods.some(
      (absenceItem) =>
        (absenceItem.reason_qualifier_one ||
          absenceItem.reason_qualifier_two) === "Newborn"
    );
    if (hasBondingReason && !hasPregnancyReason && hasNewBorn) {
      return "bonding";
    }

    if (hasPregnancyReason && !hasBondingReason) {
      return "pregnancy";
    }

    return "";
  };
  const infoAlertContext = getInfoAlertContext(absenceDetails);
  const [firstAbsenceDetail] = Object.keys(absenceDetails);

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
            absence_id: absence_case_id,
          })}
        </Alert>
      )}

      {!!infoAlertContext && (hasPendingStatus || hasApprovedStatus) && (
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
      <div>
        <Title weight="normal" small>
          {t("pages.claimsStatus.applicationDetails")}
        </Title>

        {/* Heading section */}

        <Heading level="2" size="1">
          {t("pages.claimsStatus.leaveReasonValueHeader", {
            context: findKeyByValue(LeaveReason, firstAbsenceDetail),
          })}
        </Heading>
        <div className="display-flex bg-base-lightest padding-2">
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

        {isFeatureEnabled("claimantShowPayments") && (
          <StatusNavigationTabs
            activePath={appLogic.portalFlow.pathname}
            absence_case_id={absence_case_id}
          />
        )}

        {hasPendingStatus && (
          <Timeline
            absencePeriods={claimDetail.absence_periods}
            employerFollowUpDate={
              claimDetail.managedRequirementByFollowUpDate[0]?.follow_up_date
            }
            applicationId={claimDetail.application_id}
            docList={documentsForApplication}
            absenceCaseId={claimDetail.fineos_absence_id}
            appLogic={appLogic}
          />
        )}
        <LeaveDetails absenceDetails={absenceDetails} />
        <ViewYourNotices />

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
              className="measure-6 margin-top-3"
              href={appLogic.portalFlow.getNextPageRoute(
                "UPLOAD_DOC_OPTIONS",
                {},
                { absence_case_id: claimDetail.fineos_absence_id }
              )}
            >
              {t("pages.claimsStatus.uploadDocumentsButton")}
            </ButtonLink>
          )}
        </div>

        {/* Manage applications section */}
        {(hasPendingStatus || hasApprovedStatus) && (
          <div
            className="measure-6 padding-y-4"
            data-testid="manageApplication"
          >
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

export const StatusTagMap = {
  Approved: "success",
  Denied: "error",
  Pending: "pending",
  Withdrawn: "inactive",
  Cancelled: "inactive",
} as const;

interface LeaveDetailsProps {
  absenceDetails?: Record<string, AbsencePeriod[]>;
}

export const LeaveDetails = ({ absenceDetails = {} }: LeaveDetailsProps) => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      {map(absenceDetails, (absenceItem, absenceItemName) => (
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
                    {`From ${formatDate(
                      absence_period_start_date
                    ).full()} to ${formatDate(absence_period_end_date).full()}`}
                  </p>
                  <Tag
                    label={request_decision}
                    state={StatusTagMap[request_decision]}
                  />
                  <Trans
                    i18nKey="pages.claimsStatus.leaveStatusMessage"
                    tOptions={{ context: request_decision }}
                    components={{
                      "application-link": (
                        <a
                          href={routes.applications.getReady}
                          rel="noopener noreferrer"
                          target="_blank"
                        />
                      ),
                      p: <p></p>,
                      "request-appeal-link": (
                        <a
                          href={routes.external.massgov.requestAnAppealForPFML}
                          rel="noopener noreferrer"
                          target="_blank"
                        />
                      ),
                      "request-decision-info": <p></p>,
                    }}
                  />
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
  absenceCaseId: string;
  appLogic: AppLogic;
}

export const Timeline = ({
  employerFollowUpDate = null,
  applicationId,
  docList,
  absencePeriods,
  absenceCaseId,
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

  const bondingAbsencePeriod = find(
    absencePeriods,
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
          className="measure-12"
          href={appLogic.portalFlow.getNextPageRoute(
            typeOfProof === "newborn"
              ? "UPLOAD_PROOF_OF_BIRTH"
              : "UPLOAD_PROOF_OF_PLACEMENT",
            {},
            { claim_id: applicationId, absence_case_id: absenceCaseId }
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
