import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import relationship

import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Claim, Employee, ImportLog, Payment, ReferenceFile

from ..lookup import LookupTable
from .base import Base, TimestampMixin, uuid_gen
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


class MmarsPaymentData(Base, TimestampMixin):
    __tablename__ = "mmars_payment_data"

    mmars_payment_data_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    budget_fiscal_year = Column(Integer)
    fiscal_year = Column(Integer)
    fiscal_period = Column(Integer)
    pymt_doc_code = Column(Text)
    pymt_doc_department_code = Column(Text)
    pymt_doc_unit = Column(Text)
    pymt_doc_identifier = Column(Text)
    pymt_doc_version_no = Column(Text)
    pymt_doc_vendor_line_no = Column(Text)
    pymt_doc_comm_line_no = Column(Text)
    pymt_doc_actg_line_no = Column(Text)
    pymt_actg_line_amount = Column(Numeric(asdecimal=True))
    pymt_discount_line_amount = Column(Numeric(asdecimal=True))
    pymt_penalty_line_amount = Column(Numeric(asdecimal=True))
    pymt_interest_line_amount = Column(Numeric(asdecimal=True))
    pymt_backup_withholding_line_amount = Column(Numeric(asdecimal=True))
    pymt_intercept_amount = Column(Numeric(asdecimal=True))
    pymt_retainage_line_amount = Column(Numeric(asdecimal=True))
    pymt_freight_amount = Column(Numeric(asdecimal=True))
    pymt_default_intercept_fee_amount = Column(Numeric(asdecimal=True))
    pymt_supplementary_intercept_fee_amount = Column(Numeric(asdecimal=True))
    pymt_service_from_date = Column(TIMESTAMP)
    pymt_service_to_date = Column(TIMESTAMP)
    encumbrance_doc_code = Column(Text)
    encumbrance_doc_dept = Column(Text)
    encumbrance_doc_identifier = Column(Text)
    encumbrance_vendor_line_no = Column(Text)
    encumbrance_commodity_line_no = Column(Text)
    encumbrance_accounting_line_no = Column(Text)
    disb_doc_code = Column(Text)
    disb_doc_department_code = Column(Text)
    disb_doc_identifier = Column(Text)
    disb_doc_version_no = Column(Text)
    disb_vendor_line_no = Column(Text)
    disb_commodity_line_no = Column(Text)
    disb_actg_line_no = Column(Text)
    disb_actg_line_amount = Column(Numeric(asdecimal=True))
    disb_check_amount = Column(Numeric(asdecimal=True))
    disb_discount_line_amount = Column(Numeric(asdecimal=True))
    disb_penalty_line_amount = Column(Numeric(asdecimal=True))
    disb_interest_line_amount = Column(Numeric(asdecimal=True))
    disb_backup_withholding_line_amount = Column(Numeric(asdecimal=True))
    disb_intercept_amount = Column(Numeric(asdecimal=True))
    disb_retainage_line_amount = Column(Numeric(asdecimal=True))
    disb_freight_amount = Column(Numeric(asdecimal=True))
    disb_default_intercept_fee_amount = Column(Numeric(asdecimal=True))
    disb_supplementary_intercept_fee_amount = Column(Numeric(asdecimal=True))
    disb_doc_phase_code = Column(Text)
    disb_doc_function_code = Column(Text)
    actg_line_descr = Column(Text)
    check_descr = Column(Text)
    warrant_no = Column(Text)
    warrant_select_date = Column(TIMESTAMP)
    check_eft_issue_date = Column(TIMESTAMP)
    bank_account_code = Column(Text)
    check_eft_no = Column(Text)
    cleared_date = Column(TIMESTAMP)
    appropriation = Column(Text)
    appropriation_name = Column(Text)
    object_class = Column(Text)
    object_class_name = Column(Text)
    object = Column(Text)
    object_name = Column(Text)
    income_type = Column(Text)
    income_type_name = Column(Text)
    form_type_indicator = Column(Text)
    form_typ_ind_descr = Column(Text)
    disbursement_frequency = Column(Text)
    disbursement_frequency_name = Column(Text)
    payment_lag = Column(Text)
    fund = Column(Text)
    fund_name = Column(Text)
    fund_category = Column(Text)
    fund_category_name = Column(Text)
    major_program = Column(Text)
    major_program_name = Column(Text)
    program = Column(Text)
    program_name = Column(Text)
    phase = Column(Text)
    phase_name = Column(Text)
    activity = Column(Text)
    activity_name = Column(Text)
    function = Column(Text)
    function_name = Column(Text)
    reporting = Column(Text)
    reporting_name = Column(Text)
    vendor_customer_code = Column(Text)
    legal_name = Column(Text)
    address_id = Column(Text)
    address_type = Column(Text)
    address_line_1 = Column(Text)
    address_line_2 = Column(Text)
    city = Column(Text)
    state = Column(Text)
    zip_code = Column(Text)
    country = Column(Text)
    vendor_invoice_no = Column(Text)
    vendor_invoice_date = Column(TIMESTAMP)
    scheduled_payment_date = Column(TIMESTAMP)
    doc_function_code = Column(Text)
    doc_function_code_name = Column(Text)
    doc_phase_code = Column(Text)
    doc_phase_name = Column(Text)
    government_branch = Column(Text)
    government_branch_name = Column(Text)
    cabinet = Column(Text)
    cabinet_name = Column(Text)
    department = Column(Text)
    department_name = Column(Text)
    division = Column(Text)
    division_name = Column(Text)
    Group = Column(Text)
    group_name = Column(Text)
    Section = Column(Text)
    section_name = Column(Text)
    district = Column(Text)
    district_name = Column(Text)
    bureau = Column(Text)
    bureau_name = Column(Text)
    unit = Column(Text)
    unit_name = Column(Text)
    sub_unit = Column(Text)
    sub_unit_name = Column(Text)
    doc_record_date = Column(TIMESTAMP)
    acceptance_date = Column(TIMESTAMP)
    doc_created_by = Column(Text)
    doc_created_on = Column(TIMESTAMP)
    doc_last_modified_by = Column(Text)
    doc_last_modified_on = Column(TIMESTAMP)
    NoFilter = Column(Text)
    payment_id = Column(PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True, nullable=True)

    payment = relationship(Payment)


class MmarsPaymentRefunds(Base, TimestampMixin):
    __tablename__ = "mmars_payment_refunds"

    mmars_payment_refunds_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    legal_name = Column(Text)
    vendor_customer_code = Column(Text)
    activity = Column(Text)
    activity_class = Column(Text)
    activity_class_name = Column(Text)
    activity_name = Column(Text)
    appropriation = Column(Text)
    appropriation_name = Column(Text)
    program = Column(Text)
    program_name = Column(Text)
    check_eft_no = Column(Text)
    acceptance_date = Column(TIMESTAMP)
    doc_record_date = Column(TIMESTAMP)
    posting_amount = Column(Numeric(asdecimal=True))
    debit_credit_ind = Column(Text)
    event_category = Column(Text)
    event_category_name = Column(Text)
    fund = Column(Text)
    fund_name = Column(Text)
    object = Column(Text)
    object_name = Column(Text)
    phase = Column(Text)
    phase_name = Column(Text)
    unit = Column(Text)
    unit_name = Column(Text)
    doc_code = Column(Text)
    fiscal_year = Column(Integer)
    closing_classification_code = Column(Text)

    payment_id = Column(PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True, nullable=True)

    payment = relationship(Payment)


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


class FineosWritebackDetails(Base, TimestampMixin):
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

    # == Payment Rejection Statuses
    FAILED_MANUAL_VALIDATION = LkFineosWritebackTransactionStatus(
        1, "Payment Audit Error", ACTIVE_WRITEBACK_RECORD_STATUS
    )  # Default rejection status

    DUA_ADDITIONAL_INCOME = LkFineosWritebackTransactionStatus(
        14, "DUA Additional Income", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    DIA_ADDITIONAL_INCOME = LkFineosWritebackTransactionStatus(
        15, "DIA Additional Income", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    SELF_REPORTED_ADDITIONAL_INCOME = LkFineosWritebackTransactionStatus(
        16, "SelfReported Additional Income", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    EXEMPT_EMPLOYER = LkFineosWritebackTransactionStatus(
        17, "Exempt Employer", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    WEEKLY_BENEFITS_AMOUNT_EXCEEDS_850 = LkFineosWritebackTransactionStatus(
        18, "Max Weekly Benefits Exceeded", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    WAITING_WEEK = LkFineosWritebackTransactionStatus(
        19, "InvalidPayment WaitingWeek", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    ALREADY_PAID_FOR_DATES = LkFineosWritebackTransactionStatus(
        20, "InvalidPayment PaidDate", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    LEAVE_DATES_CHANGE = LkFineosWritebackTransactionStatus(
        21, "InvalidPayment LeaveDateChange", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    UNDER_OR_OVERPAY_ADJUSTMENT = LkFineosWritebackTransactionStatus(
        22, "InvalidPayment PayAdjustment", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    NAME_MISMATCH = LkFineosWritebackTransactionStatus(
        23, "InvalidPayment NameMismatch", ACTIVE_WRITEBACK_RECORD_STATUS
    )


class AuditReportAction(str, Enum):
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"
    INFORMATIONAL = "INFORMATIONAL"
    # These below actions are for scenarios where
    # we want to default to skipped/rejected, but
    # the details we put in the reject notes are sufficient
    # and don't require populating an additional column
    SKIPPED_NO_COLUMN = "SKIPPED_NO_COLUMN"
    REJECTED_NO_COLUMN = "REJECTED_NO_COLUMN"
    INFORMATIONAL_NO_COLUMN = "INFORMATIONAL_NO_COLUMN"

    # These below methods help us group the behavior
    # of these actions by effectively mapping the string
    # value to the enum

    @staticmethod
    def should_populate_column(audit_report_action_str: str) -> bool:
        if audit_report_action_str in [
            AuditReportAction.SKIPPED_NO_COLUMN,
            AuditReportAction.REJECTED_NO_COLUMN,
            AuditReportAction.INFORMATIONAL_NO_COLUMN,
        ]:
            return False
        return True

    @staticmethod
    def is_rejected(audit_report_action_str: str) -> bool:
        if audit_report_action_str in [
            AuditReportAction.REJECTED,
            AuditReportAction.REJECTED_NO_COLUMN,
        ]:
            return True
        return False

    @staticmethod
    def is_skipped(audit_report_action_str: str) -> bool:
        if audit_report_action_str in [
            AuditReportAction.SKIPPED,
            AuditReportAction.SKIPPED_NO_COLUMN,
        ]:
            return True
        return False

    @staticmethod
    def is_informational(audit_report_action_str: str) -> bool:
        if audit_report_action_str in [
            AuditReportAction.INFORMATIONAL,
            audit_report_action_str == AuditReportAction.INFORMATIONAL_NO_COLUMN,
        ]:
            return True
        return False


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
        1, "Max Weekly Benefits", AuditReportAction.REJECTED
    )
    DUA_DIA_REDUCTION = LkPaymentAuditReportType(
        2, "DUA DIA Reduction", AuditReportAction.INFORMATIONAL
    )
    LEAVE_PLAN_IN_REVIEW = LkPaymentAuditReportType(
        3, "Leave Plan In Review", AuditReportAction.SKIPPED_NO_COLUMN
    )
    DOR_FINEOS_NAME_MISMATCH = LkPaymentAuditReportType(
        4, "DOR FINEOS Name Mismatch", AuditReportAction.INFORMATIONAL
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


class Pfml1099MMARSPayment(Base, TimestampMixin):
    __tablename__ = "pfml_1099_mmars_payment"
    pfml_1099_mmars_payment_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    pfml_1099_batch_id = Column(
        PostgreSQLUUID, ForeignKey("pfml_1099_batch.pfml_1099_batch_id"), index=True, nullable=False
    )
    mmars_payment_id = Column(Integer, nullable=False)
    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True, nullable=False
    )
    payment_amount = Column(Numeric, nullable=False)
    payment_date = Column(Date, nullable=False)

    employee = relationship(Employee)


class Pfml1099Payment(Base, TimestampMixin):
    __tablename__ = "pfml_1099_payment"
    pfml_1099_payment_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    pfml_1099_batch_id = Column(
        PostgreSQLUUID, ForeignKey("pfml_1099_batch.pfml_1099_batch_id"), index=True, nullable=False
    )
    payment_id = Column(
        PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True, nullable=False
    )
    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), index=True, nullable=False)
    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True, nullable=False
    )
    payment_amount = Column(Numeric, nullable=False)
    payment_date = Column(Date, nullable=False)

    payment = relationship(Payment)
    claim = relationship(Claim)
    employee = relationship(Employee)


class Pfml1099Batch(Base, TimestampMixin):
    __tablename__ = "pfml_1099_batch"
    pfml_1099_batch_id = Column(PostgreSQLUUID, primary_key=True, nullable=False)
    tax_year = Column(Integer, nullable=False)
    batch_run_date = Column(Date, nullable=False)
    correction_ind = Column(Boolean, nullable=False)


class Pfml1099Withholding(Base, TimestampMixin):
    __tablename__ = "pfml_1099_withholding"
    pfml_1099_withholding_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    pfml_1099_batch_id = Column(
        PostgreSQLUUID, ForeignKey("pfml_1099_batch.pfml_1099_batch_id"), index=True, nullable=False
    )
    payment_id = Column(
        PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True, nullable=False
    )
    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), index=True, nullable=False)
    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True, nullable=False
    )
    withholding_amount = Column(Numeric, nullable=False)
    withholding_date = Column(Date, nullable=False)

    payment = relationship(Payment)
    claim = relationship(Claim)
    employee = relationship(Employee)


class Pfml1099Refund(Base, TimestampMixin):
    __tablename__ = "pfml_1099_refund"
    pfml_1099_refund_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    pfml_1099_batch_id = Column(
        PostgreSQLUUID, ForeignKey("pfml_1099_batch.pfml_1099_batch_id"), index=True, nullable=False
    )
    payment_id = Column(
        PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True, nullable=False
    )
    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True, nullable=False
    )
    refund_amount = Column(Numeric, nullable=False)
    refund_date = Column(Date, nullable=False)

    payment = relationship(Payment)
    employee = relationship(Employee)


class Pfml1099(Base, TimestampMixin):
    __tablename__ = "pfml_1099"
    pfml_1099_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    pfml_1099_batch_id = Column(
        PostgreSQLUUID, ForeignKey("pfml_1099_batch.pfml_1099_batch_id"), index=True, nullable=False
    )
    tax_year = Column(Integer, nullable=False)
    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True, nullable=False
    )
    tax_identifier_id = Column(PostgreSQLUUID, nullable=False)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    address_line_1 = Column(Text, nullable=False)
    address_line_2 = Column(Text, nullable=False)
    city = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    zip = Column(Text, nullable=False)
    gross_payments = Column(Numeric(asdecimal=True), nullable=False)
    state_tax_withholdings = Column(Numeric(asdecimal=True), nullable=False)
    federal_tax_withholdings = Column(Numeric(asdecimal=True), nullable=False)
    overpayment_repayments = Column(Numeric(asdecimal=True), nullable=False)
    correction_ind = Column(Boolean, nullable=False)

    employee = relationship(Employee)


def sync_maximum_weekly_benefit_amount(db_session):
    maximum_weekly_benefit_amounts = [
        MaximumWeeklyBenefitAmount(datetime.date(2020, 10, 1), "850.00"),
    ]

    for maximum_weekly_benefit_amount in maximum_weekly_benefit_amounts:
        instance = db_session.merge(maximum_weekly_benefit_amount)
        if db_session.is_modified(instance):
            logger.info("updating maximum weekly benefit amount %r", instance)

    db_session.commit()
