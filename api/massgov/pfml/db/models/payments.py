import datetime
from decimal import Decimal

from sqlalchemy import JSON, TIMESTAMP, Column, Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import now as sqlnow

import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import ImportLog, Payment, ReferenceFile

from ..lookup import LookupTable
from .base import Base, TimestampMixin, utc_timestamp_gen, uuid_gen
from .common import PostgreSQLUUID

logger = massgov.pfml.util.logging.get_logger(__name__)


class FineosExtractVpei(Base, TimestampMixin):
    __tablename__ = "fineos_extract_vpei"

    vpei_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    c = Column(Text)
    i = Column(Text)
    lastupdatedate = Column(Text)
    c_osuser_updatedby = Column(Text)
    i_osuser_updatedby = Column(Text)
    addressline1 = Column(Text)
    addressline2 = Column(Text)
    addressline3 = Column(Text)
    addressline4 = Column(Text)
    addressline5 = Column(Text)
    addressline6 = Column(Text)
    addressline7 = Column(Text)
    advicetopay = Column(Text)
    advicetopayov = Column(Text)
    amalgamationc = Column(Text)
    amount_monamt = Column(Text)
    amount_moncur = Column(Text)
    checkcutting = Column(Text)
    confirmedbyus = Column(Text)
    confirmeduid = Column(Text)
    contractref = Column(Text)
    correspcountr = Column(Text)
    currency = Column(Text)
    dateinterface = Column(Text)
    description = Column(Text)
    employeecontr = Column(Text)
    eventeffectiv = Column(Text)
    eventreason = Column(Text)
    eventtype = Column(Text)
    extractiondat = Column(Text)
    grosspaymenta_monamt = Column(Text)
    grosspaymenta_moncur = Column(Text)
    insuredreside = Column(Text)
    nametoprinton = Column(Text)
    nominatedpaye = Column(Text)
    nompayeecusto = Column(Text)
    nompayeedob = Column(Text)
    nompayeefulln = Column(Text)
    nompayeesocnu = Column(Text)
    notes = Column(Text)
    payeeaccountn = Column(Text)
    payeeaccountt = Column(Text)
    payeeaddress = Column(Text)
    payeebankbran = Column(Text)
    payeebankcode = Column(Text)
    payeebankinst = Column(Text)
    payeebanksort = Column(Text)
    payeecorrespo = Column(Text)
    payeecustomer = Column(Text)
    payeedob = Column(Text)
    payeefullname = Column(Text)
    payeeidentifi = Column(Text)
    payeesocnumbe = Column(Text)
    paymentadd = Column(Text)
    paymentadd1 = Column(Text)
    paymentadd2 = Column(Text)
    paymentadd3 = Column(Text)
    paymentadd4 = Column(Text)
    paymentadd5 = Column(Text)
    paymentadd6 = Column(Text)
    paymentadd7 = Column(Text)
    paymentaddcou = Column(Text)
    paymentcorrst = Column(Text)
    paymentdate = Column(Text)
    paymentfreque = Column(Text)
    paymentmethod = Column(Text)
    paymentpostco = Column(Text)
    paymentpremis = Column(Text)
    paymenttrigge = Column(Text)
    paymenttype = Column(Text)
    paymethcurren = Column(Text)
    postcode = Column(Text)
    premisesno = Column(Text)
    setupbyuserid = Column(Text)
    setupbyuserna = Column(Text)
    status = Column(Text)
    statuseffecti = Column(Text)
    statusreason = Column(Text)
    stockno = Column(Text)
    summaryeffect = Column(Text)
    summarystatus = Column(Text)
    transstatusda = Column(Text)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    reference_file = relationship(ReferenceFile)


class FineosExtractVpeiPaymentDetails(Base, TimestampMixin):
    __tablename__ = "fineos_extract_vpei_payment_details"

    vpei_payment_details_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    c = Column(Text)
    i = Column(Text)
    lastupdatedate = Column(Text)
    c_osuser_updatedby = Column(Text)
    i_osuser_updatedby = Column(Text)
    benefiteffect = Column(Text)
    benefitfinalp = Column(Text)
    description_paymentdtls = Column(Text)
    paymentendper = Column(Text)
    paymentstartp = Column(Text)
    balancingamou_monamt = Column(Text)
    balancingamou_moncur = Column(Text)
    businessnetbe_monamt = Column(Text)
    businessnetbe_moncur = Column(Text)
    duetype = Column(Text)
    groupid = Column(Text)
    peclassid = Column(Text)
    peindexid = Column(Text)
    claimdetailsclassid = Column(Text)
    claimdetailsindexid = Column(Text)
    dateinterface = Column(Text)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    reference_file = relationship(ReferenceFile)


class FineosExtractVpeiClaimDetails(Base, TimestampMixin):
    __tablename__ = "fineos_extract_vpei_claim_details"

    vpei_claim_details_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    c = Column(Text)
    i = Column(Text)
    lastupdatedate = Column(Text)
    c_osuser_updatedby = Column(Text)
    i_osuser_updatedby = Column(Text)
    absencecasenu = Column(Text)
    benefitrightt = Column(Text)
    claimantage = Column(Text)
    claimantcusto = Column(Text)
    claimantdob = Column(Text)
    claimantgende = Column(Text)
    claimantname = Column(Text)
    claimantrelto = Column(Text)
    claimnumber = Column(Text)
    diagcode2 = Column(Text)
    diagcode3 = Column(Text)
    diagcode4 = Column(Text)
    diagcode5 = Column(Text)
    employeeid = Column(Text)
    eventcause = Column(Text)
    incurreddate = Column(Text)
    insuredaddres = Column(Text)
    insuredaddrl1 = Column(Text)
    insuredaddrl2 = Column(Text)
    insuredaddrl3 = Column(Text)
    insuredaddrl4 = Column(Text)
    insuredaddrl5 = Column(Text)
    insuredaddrl6 = Column(Text)
    insuredaddrl7 = Column(Text)
    insuredage = Column(Text)
    insuredcorcou = Column(Text)
    insuredcorres = Column(Text)
    insuredcustom = Column(Text)
    insureddob = Column(Text)
    insuredemploy = Column(Text)
    insuredfullna = Column(Text)
    insuredgender = Column(Text)
    insuredpostco = Column(Text)
    insuredpremis = Column(Text)
    insuredretire = Column(Text)
    insuredsocnum = Column(Text)
    leaveplanid = Column(Text)
    leaverequesti = Column(Text)
    notifieddate = Column(Text)
    payeeageatinc = Column(Text)
    payeecaserole = Column(Text)
    payeereltoins = Column(Text)
    primarydiagno = Column(Text)
    primarymedica = Column(Text)
    diag2medicalc = Column(Text)
    diag3medicalc = Column(Text)
    diag4medicalc = Column(Text)
    diag5medicalc = Column(Text)
    peclassid = Column(Text)
    peindexid = Column(Text)
    dateinterface = Column(Text)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    reference_file = relationship(ReferenceFile)


class FineosExtractVbiRequestedAbsenceSom(Base, TimestampMixin):
    __tablename__ = "fineos_extract_vbi_requested_absence_som"

    vbi_requested_absence_som_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    notification_casenumber = Column(Text)
    absence_casenumber = Column(Text)
    absence_casetypename = Column(Text)
    absence_casestatus = Column(Text)
    absence_caseowner = Column(Text)
    absence_casecreationdate = Column(Text)
    absence_caselastupdatedate = Column(Text)
    absence_intakesource = Column(Text)
    absence_notifiedby = Column(Text)
    employee_customerno = Column(Text)
    employee_manager_customerno = Column(Text)
    employee_addtl_mngr_customerno = Column(Text)
    employer_customerno = Column(Text)
    employer_name = Column(Text)
    employment_classid = Column(Text)
    employment_indexid = Column(Text)
    leaverequest_id = Column(Text)
    leaverequest_notificationdate = Column(Text)
    leaverequest_lastupdatedate = Column(Text)
    leaverequest_originalrequest = Column(Text)
    leaverequest_evidenceresulttype = Column(Text)
    leaverequest_decision = Column(Text)
    leaverequest_diagnosis = Column(Text)
    absencereason_classid = Column(Text)
    absencereason_indexid = Column(Text)
    absencereason_name = Column(Text)
    absencereason_qualifier1 = Column(Text)
    absencereason_qualifier2 = Column(Text)
    absencereason_coverage = Column(Text)
    primary_relationship_name = Column(Text)
    primary_relationship_qual1 = Column(Text)
    primary_relationship_qual2 = Column(Text)
    primary_relationship_cover = Column(Text)
    secondary_relationship_name = Column(Text)
    secondary_relationship_qual1 = Column(Text)
    secondary_relationship_qual2 = Column(Text)
    secondary_relationship_cover = Column(Text)
    absenceperiod_classid = Column(Text)
    absenceperiod_indexid = Column(Text)
    absenceperiod_type = Column(Text)
    absenceperiod_status = Column(Text)
    absenceperiod_start = Column(Text)
    absenceperiod_end = Column(Text)
    episode_frequency_count = Column(Text)
    episode_frequency_period = Column(Text)
    episodic_frequency_period_unit = Column(Text)
    episode_duration = Column(Text)
    episodic_duration_unit = Column(Text)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )
    reference_file = relationship(ReferenceFile)


class FineosExtractVbiRequestedAbsence(Base, TimestampMixin):
    __tablename__ = "fineos_extract_vbi_requested_absence"

    vbi_requested_absence_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    notification_casenumber = Column(Text)
    absence_casenumber = Column(Text)
    absence_casetypename = Column(Text)
    absence_casestatus = Column(Text)
    absence_caseowner = Column(Text)
    absence_casecreationdate = Column(Text)
    absence_caselastupdatedate = Column(Text)
    absence_intakesource = Column(Text)
    absence_notifiedby = Column(Text)
    employee_customerno = Column(Text)
    employee_manager_customerno = Column(Text)
    employee_addtl_mngr_customerno = Column(Text)
    employer_customerno = Column(Text)
    employer_name = Column(Text)
    employment_classid = Column(Text)
    employment_indexid = Column(Text)
    leaverequest_id = Column(Text)
    leaverequest_notificationdate = Column(Text)
    leaverequest_lastupdatedate = Column(Text)
    leaverequest_originalrequest = Column(Text)
    leaverequest_decision = Column(Text)
    leaverequest_diagnosis = Column(Text)
    absencereason_classid = Column(Text)
    absencereason_indexid = Column(Text)
    absencereason_name = Column(Text)
    absencereason_qualifier1 = Column(Text)
    absencereason_qualifier2 = Column(Text)
    absencereason_coverage = Column(Text)
    primary_relationship_name = Column(Text)
    primary_relationship_qual1 = Column(Text)
    primary_relationship_qual2 = Column(Text)
    primary_relationship_cover = Column(Text)
    secondary_relationship_name = Column(Text)
    secondary_relationship_qual1 = Column(Text)
    secondary_relationship_qual2 = Column(Text)
    secondary_relationship_cover = Column(Text)
    absenceperiod_classid = Column(Text)
    absenceperiod_indexid = Column(Text)
    absenceperiod_type = Column(Text)
    absenceperiod_status = Column(Text)
    absenceperiod_start = Column(Text)
    absenceperiod_end = Column(Text)
    episode_frequency_count = Column(Text)
    episode_frequency_period = Column(Text)
    episodic_frequency_period_unit = Column(Text)
    episode_duration = Column(Text)
    episodic_duration_unit = Column(Text)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )
    reference_file = relationship(ReferenceFile)


class FineosExtractEmployeeFeed(Base, TimestampMixin):
    __tablename__ = "fineos_extract_employee_feed"

    employee_feed_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    c = Column(Text)
    i = Column(Text)
    lastupdatedate = Column(Text)
    firstnames = Column(Text)
    initials = Column(Text)
    lastname = Column(Text)
    placeofbirth = Column(Text)
    dateofbirth = Column(Text)
    dateofdeath = Column(Text)
    isdeceased = Column(Text)
    realdob = Column(Text)
    title = Column(Text)
    nationality = Column(Text)
    countryofbirt = Column(Text)
    sex = Column(Text)
    maritalstatus = Column(Text)
    disabled = Column(Text)
    natinsno = Column(Text)
    customerno = Column(Text)
    referenceno = Column(Text)
    identificatio = Column(Text)
    unverified = Column(Text)
    staff = Column(Text)
    groupclient = Column(Text)
    securedclient = Column(Text)
    selfserviceen = Column(Text)
    sourcesystem = Column(Text)
    c_ocprtad_correspondenc = Column(Text)
    i_ocprtad_correspondenc = Column(Text)
    extconsent = Column(Text)
    extconfirmflag = Column(Text)
    extmassid = Column(Text)
    extoutofstateid = Column(Text)
    preferredcont = Column(Text)
    c_bnkbrnch_bankbranch = Column(Text)
    i_bnkbrnch_bankbranch = Column(Text)
    preferred_contact_method = Column(Text)
    defpaymentpref = Column(Text)
    payment_preference = Column(Text)
    paymentmethod = Column(Text)
    paymentaddres = Column(Text)
    address1 = Column(Text)
    address1 = Column(Text)
    address2 = Column(Text)
    address3 = Column(Text)
    address4 = Column(Text)
    address5 = Column(Text)
    address6 = Column(Text)
    address7 = Column(Text)
    postcode = Column(Text)
    country = Column(Text)
    verifications = Column(Text)
    accountname = Column(Text)
    accountno = Column(Text)
    bankcode = Column(Text)
    sortcode = Column(Text)
    accounttype = Column(Text)
    active_absence_flag = Column(Text)

    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    reference_file = relationship(ReferenceFile)


class MaximumWeeklyBenefitAmount(Base):
    # See regulations for how this is calculated:
    # https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXXII/Chapter175M/Section3
    __tablename__ = "maximum_weekly_benefit_amount"

    effective_date = Column(Date, primary_key=True, nullable=False)
    maximum_weekly_benefit_amount = Column(Numeric, nullable=False)

    def __init__(self, effective_date: datetime.date, maximum_weekly_benefit_amount: str):
        """ Constructor takes metric as a string to maintain precision. """

        self.effective_date = effective_date
        self.maximum_weekly_benefit_amount = Decimal(maximum_weekly_benefit_amount)


class FineosWritebackDetails(Base):
    __tablename__ = "fineos_writeback_details"
    fineos_writeback_details_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    payment_id = Column(
        PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True, nullable=False
    )

    transaction_status_id = Column(
        Integer,
        ForeignKey("lk_fineos_writeback_transaction_status.transaction_status_id"),
        nullable=False,
    )
    import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )
    writeback_sent_at = Column(TIMESTAMP(timezone=True), nullable=True,)

    payment = relationship(Payment)
    transaction_status = relationship("LkFineosWritebackTransactionStatus")
    import_log = relationship(ImportLog)


class LkFineosWritebackTransactionStatus(Base):
    __tablename__ = "lk_fineos_writeback_transaction_status"
    transaction_status_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_status_description = Column(Text, nullable=False)
    writeback_record_status = Column(Text)

    def __init__(
        self, transaction_status_id, transaction_status_description, writeback_record_status
    ):
        if len(transaction_status_description) > 30:
            raise Exception(
                "FINEOS limits transaction statuses to a maximum of 30 characters, we cannot use %s"
                % transaction_status_description
            )

        self.transaction_status_id = transaction_status_id
        self.transaction_status_description = transaction_status_description
        self.writeback_record_status = writeback_record_status


ACTIVE_WRITEBACK_RECORD_STATUS = "Active"
PENDING_ACTIVE_WRITEBACK_RECORD_STATUS = (
    ""  # To keep a payment in pending active, we don't set the value
)


class PaymentLog(Base, TimestampMixin):
    __tablename__ = "payment_log"
    payment_log_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    payment_id = Column(
        PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True, nullable=False
    )

    import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)

    details = Column(JSON)

    payment = relationship(Payment)
    import_log = relationship(ImportLog)


class FineosWritebackTransactionStatus(LookupTable):
    model = LkFineosWritebackTransactionStatus
    column_names = (
        "transaction_status_id",
        "transaction_status_description",
        "writeback_record_status",
    )

    FAILED_MANUAL_VALIDATION = LkFineosWritebackTransactionStatus(
        1, "Payment Audit Error", ACTIVE_WRITEBACK_RECORD_STATUS
    )
    FAILED_AUTOMATED_VALIDATION = LkFineosWritebackTransactionStatus(
        2, "Payment Validation Error", ACTIVE_WRITEBACK_RECORD_STATUS
    )
    PRENOTE_ERROR = LkFineosWritebackTransactionStatus(
        3, "EFT Account Information Error", ACTIVE_WRITEBACK_RECORD_STATUS
    )
    PENDING_PRENOTE = LkFineosWritebackTransactionStatus(
        4, "EFT Pending Bank Validation", PENDING_ACTIVE_WRITEBACK_RECORD_STATUS
    )
    DATA_ISSUE_IN_SYSTEM = LkFineosWritebackTransactionStatus(
        5, "Payment System Error", PENDING_ACTIVE_WRITEBACK_RECORD_STATUS
    )
    TOTAL_BENEFITS_OVER_CAP = LkFineosWritebackTransactionStatus(
        6, "Max Weekly Benefits Exceeded", ACTIVE_WRITEBACK_RECORD_STATUS
    )
    ADDRESS_VALIDATION_ERROR = LkFineosWritebackTransactionStatus(
        7, "Address Validation Error", ACTIVE_WRITEBACK_RECORD_STATUS
    )
    PENDING_PAYMENT_AUDIT = LkFineosWritebackTransactionStatus(
        8, "Pending Payment Audit", PENDING_ACTIVE_WRITEBACK_RECORD_STATUS
    )
    BANK_PROCESSING_ERROR = LkFineosWritebackTransactionStatus(
        9, "Bank Processing Error", ACTIVE_WRITEBACK_RECORD_STATUS
    )
    PROCESSED = LkFineosWritebackTransactionStatus(10, "Processed", ACTIVE_WRITEBACK_RECORD_STATUS)
    PAID = LkFineosWritebackTransactionStatus(11, "Paid", ACTIVE_WRITEBACK_RECORD_STATUS)
    POSTED = LkFineosWritebackTransactionStatus(12, "Posted", ACTIVE_WRITEBACK_RECORD_STATUS)
    LEAVE_IN_REVIEW = LkFineosWritebackTransactionStatus(
        13, "Leave Plan In Review", PENDING_ACTIVE_WRITEBACK_RECORD_STATUS
    )


PAYMENT_AUDIT_REPORT_ACTION_REJECTED = "REJECTED"
PAYMENT_AUDIT_REPORT_ACTION_SKIPPED = "SKIPPED"
PAYMENT_AUDIT_REPORT_ACTION_INFORMATIONAL = ""


class LkPaymentAuditReportType(Base):
    __tablename__ = "lk_payment_audit_report_type"
    payment_audit_report_type_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_audit_report_type_description = Column(Text, nullable=False)
    payment_audit_report_action = Column(Text, nullable=False)

    def __init__(
        self,
        payment_audit_report_type_id,
        payment_audit_report_type_description,
        payment_audit_report_action,
    ):
        self.payment_audit_report_type_id = payment_audit_report_type_id
        self.payment_audit_report_type_description = payment_audit_report_type_description
        self.payment_audit_report_action = payment_audit_report_action


class PaymentAuditReportType(LookupTable):
    model = LkPaymentAuditReportType
    column_names = (
        "payment_audit_report_type_id",
        "payment_audit_report_type_description",
        "payment_audit_report_action",
    )

    MAX_WEEKLY_BENEFITS = LkPaymentAuditReportType(
        1, "Max Weekly Benefits", PAYMENT_AUDIT_REPORT_ACTION_REJECTED
    )
    DUA_DIA_REDUCTION = LkPaymentAuditReportType(
        2, "DUA DIA Reduction", PAYMENT_AUDIT_REPORT_ACTION_SKIPPED
    )


class PaymentAuditReportDetails(Base, TimestampMixin):
    __tablename__ = "payment_audit_details"
    payment_audit_details_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    payment_id = Column(
        PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True, nullable=False
    )
    audit_report_type_id = Column(
        Integer,
        ForeignKey("lk_payment_audit_report_type.payment_audit_report_type_id"),
        nullable=False,
    )
    details = Column(JSON, nullable=False)
    added_to_audit_report_at = Column(TIMESTAMP(timezone=True), nullable=True,)
    import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)

    payment = relationship(Payment)
    audit_report_type = relationship(LkPaymentAuditReportType)
    import_log = relationship(ImportLog)


def sync_lookup_tables(db_session):
    FineosWritebackTransactionStatus.sync_to_database(db_session)
    PaymentAuditReportType.sync_to_database(db_session)


def sync_maximum_weekly_benefit_amount(db_session):
    maximum_weekly_benefit_amounts = [
        MaximumWeeklyBenefitAmount(datetime.date(2020, 10, 1), "850.00"),
    ]

    for maximum_weekly_benefit_amount in maximum_weekly_benefit_amounts:
        instance = db_session.merge(maximum_weekly_benefit_amount)
        if db_session.is_modified(instance):
            logger.info("updating maximum weekly benefit amount %r", instance)

    db_session.commit()
