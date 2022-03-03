from enum import Enum
from typing import Optional, cast

from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Index

import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Claim, Employee, ImportLog, Payment, ReferenceFile

from ..lookup import LookupTable
from .base import Base, TimestampMixin, deprecated_column, uuid_gen
from .common import PostgreSQLUUID
from .common import XMLType as XML

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
    peclassid = Column(Text, index=True)
    peindexid = Column(Text, index=True)
    claimdetailsclassid = Column(Text)
    claimdetailsindexid = Column(Text)
    dateinterface = Column(Text)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    Index(
        "ix_payment_details_c_i_reference_file_id",
        fineos_extract_import_log_id,
        peclassid,
        peindexid,
        unique=False,
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
    peclassid = Column(Text, index=True)
    peindexid = Column(Text, index=True)
    dateinterface = Column(Text)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    Index(
        "ix_claim_details_c_i_reference_file_id",
        fineos_extract_import_log_id,
        peclassid,
        peindexid,
        unique=False,
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
    orgunit_name = Column(Text)
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
    leaverequest_id = Column(Text, index=True)
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

    Index(
        "ix_payment_details_leaverequest_reference_file_id",
        fineos_extract_import_log_id,
        leaverequest_id,
        unique=False,
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
    customerno = Column(Text, index=True)
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
    effectivefrom = Column(Text)
    effectiveto = Column(Text)

    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )

    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    Index(
        "ix_employee_feed_import_log_id_customerno",
        fineos_extract_import_log_id,
        customerno,
        unique=False,
    )

    reference_file = relationship(ReferenceFile)


class FineosExtractPaymentFullSnapshot(Base, TimestampMixin):
    __tablename__ = "fineos_extract_payment_full_snapshot"

    payment_report_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    c = Column(Text)
    i = Column(Text)
    flags = Column(Text)
    partitionid = Column(Text)
    lastupdatedate = Column(Text)
    boeversion = Column(Text)
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
    datelastproce = Column(Text)
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
    percenttaxabl = Column(Text)
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
    taxoverride = Column(Text)
    taxwageamount_monamt = Column(Text)
    taxwageamount_moncur = Column(Text)
    transactionno = Column(Text)
    transactionst = Column(Text)
    transstatusda = Column(Text)

    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    reference_file = relationship(ReferenceFile)


class FineosExtractCancelledPayments(Base, TimestampMixin):
    __tablename__ = "fineos_extract_cancelled_payments"

    canelled_payment_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    c = Column(Text)
    i = Column(Text)
    statusreason = Column(Text)
    grossamount = Column(Text)
    addedby = Column(Text)
    issuedate = Column(Text)
    cancellationdate = Column(Text)
    transactionstatusdate = Column(Text)
    transactionstatus = Column(Text)
    extractiondate = Column(Text)
    stocknumber = Column(Text)
    claimnumber = Column(Text)
    benefitcasenumber = Column(Text)

    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    reference_file = relationship(ReferenceFile)


class FineosExtractReplacedPayments(Base, TimestampMixin):
    __tablename__ = "fineos_extract_replaced_payments"

    replaced_payment_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    c = Column(Text)
    i = Column(Text)
    statusreason = Column(Text)
    grossamount = Column(Text)
    addedby = Column(Text)
    issuedate = Column(Text)
    cancellationdate = Column(Text)
    transactionstatusdate = Column(Text)
    transactionstatus = Column(Text)
    extractiondate = Column(Text)
    stocknumber = Column(Text)
    claimnumber = Column(Text)
    benefitcasenumber = Column(Text)

    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    reference_file = relationship(ReferenceFile)


class FineosExtractVbiLeavePlanRequestedAbsence(Base, TimestampMixin):
    __tablename__ = "fineos_extract_vbi_leave_plan_requested_absence"

    leave_plan_requested_absence_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    selectedplan_classid = Column(Text)
    selectedplan_indexid = Column(Text)
    selectedplan_lastupdatedate = Column(Text)
    selectedplan_adjudicat_result = Column(Text)
    selectedplan_adjudication_note = Column(Text)
    selectedplan_updatedbyuserid = Column(Text)
    leaveplan_classid = Column(Text)
    leaveplan_indexid = Column(Text)
    leaveplan_displayreference = Column(Text)
    leaveplan_shortname = Column(Text)
    leaveplan_longname = Column(Text)
    leaveplan_alias = Column(Text)
    leaveplan_leavegroup = Column(Text)
    leaveplan_leavecategory = Column(Text)
    leaveplan_leavetype = Column(Text)
    leaveplan_state = Column(Text)
    leaveplan_jobprotection = Column(Text)
    leaverequest_id = Column(Text)

    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    reference_file = relationship(ReferenceFile)


class FineosExtractVPaidLeaveInstruction(Base, TimestampMixin):
    __tablename__ = "fineos_extract_v_paid_leave_instruction"

    paid_leave_instruction_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    c = Column(Text)
    i = Column(Text)
    flags = Column(Text)
    partitionid = Column(Text)
    lastupdatedate = Column(Text)
    boeversion = Column(Text)
    c_osuser_updatedby = Column(Text)
    i_osuser_updatedby = Column(Text)
    averagedaysworked = Column(Text)
    averageweeklywage_monamt = Column(Text)
    averageweeklywage_moncur = Column(Text)
    benefitwaitingperiod = Column(Text)
    doesmandatoryfitapply = Column(Text)
    notes = Column(Text)
    policyreference = Column(Text)
    taxablepercentage = Column(Text)
    autoapprovebenefits = Column(Text)
    benefitwaitingperiodbasis = Column(Text)
    c_selectedleaveplan = Column(Text)
    i_selectedleaveplan = Column(Text)

    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    reference_file = relationship(ReferenceFile)


class FineosExtractVbi1099DataSom(Base, TimestampMixin):
    __tablename__ = "fineos_extract_vbi_1099_data_som"
    vbi_1099_data_som_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    firstnames = Column(Text)
    lastname = Column(Text)
    customerno = Column(Text)
    packeddata = Column(XML)
    documenttype = Column(Text)
    c = Column(Text)

    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )

    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )

    Index(
        "ix_vbi_1099_data_som_import_log_id_customerno",
        fineos_extract_import_log_id,
        customerno,
        unique=False,
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
    payment_id = deprecated_column(
        PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True, nullable=True
    )

    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), index=True, nullable=True)
    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True, nullable=True
    )
    payment_i_value = Column(Text)

    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), index=True, nullable=True)
    claim = relationship(Claim)

    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True, nullable=True
    )
    employee = relationship(Employee)
    payment_i_value = Column(Text)


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

    payment = relationship(Payment, back_populates="fineos_writeback_details")
    transaction_status = relationship("LkFineosWritebackTransactionStatus")
    import_log = relationship(ImportLog)


# Because of how the app is loaded, we need
# to define this here, after both classes are registered
Payment.fineos_writeback_details = relationship(  # type: ignore
    FineosWritebackDetails, back_populates="payment", order_by="FineosWritebackDetails.created_at",
)


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
    DEPRECATED_TOTAL_BENEFITS_OVER_CAP = LkFineosWritebackTransactionStatus(
        6, "Max Weekly Benefits Exceeded", ACTIVE_WRITEBACK_RECORD_STATUS
    )  # Duplicate of 18 - WEEKLY_BENEFITS_AMOUNT_EXCEEDS_850, use that instead
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

    WITHHOLDING_ERROR = LkFineosWritebackTransactionStatus(
        24, "PrimaryPayment ProcessingErr", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    PAYMENT_AUDIT_IN_PROGRESS = LkFineosWritebackTransactionStatus(
        25, "Payment Audit In Progress", PENDING_ACTIVE_WRITEBACK_RECORD_STATUS
    )

    VOID_CHECK = LkFineosWritebackTransactionStatus(
        26, "PUB Check Voided", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    STOP_CHECK = LkFineosWritebackTransactionStatus(
        27, "PUB Check Undeliverable", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    STALE_CHECK = LkFineosWritebackTransactionStatus(
        28, "PUB Check Stale", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    LEAVE_DURATION_MAX_EXCEEDED = LkFineosWritebackTransactionStatus(
        29, "Max Leave Duration Exceeded", ACTIVE_WRITEBACK_RECORD_STATUS
    )

    INVALID_ROUTING_NUMBER = LkFineosWritebackTransactionStatus(
        30, "Invalid Routing Number", PENDING_ACTIVE_WRITEBACK_RECORD_STATUS
    )


class AuditReportAction(str, Enum):
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"
    INFORMATIONAL = "INFORMATIONAL"


class LkPaymentAuditReportType(Base):
    __tablename__ = "lk_payment_audit_report_type"
    payment_audit_report_type_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_audit_report_type_description = Column(Text, nullable=False)
    payment_audit_report_action = Column(Text, nullable=False)
    payment_audit_report_column = Column(Text, nullable=True)

    def __init__(
        self,
        payment_audit_report_type_id,
        payment_audit_report_type_description,
        payment_audit_report_action,
        payment_audit_report_column,
    ):
        self.payment_audit_report_type_id = payment_audit_report_type_id
        self.payment_audit_report_type_description = payment_audit_report_type_description
        self.payment_audit_report_action = payment_audit_report_action
        self.payment_audit_report_column = payment_audit_report_column


class PaymentAuditReportType(LookupTable):
    model = LkPaymentAuditReportType
    column_names = (
        "payment_audit_report_type_id",
        "payment_audit_report_type_description",
        "payment_audit_report_action",
        "payment_audit_report_column",
    )

    DEPRECATED_MAX_WEEKLY_BENEFITS = LkPaymentAuditReportType(
        1, "Deprecated - Max Weekly Benefits", AuditReportAction.REJECTED, None,
    )
    DEPRECATED_DUA_DIA_REDUCTION = LkPaymentAuditReportType(
        2, "Deprecated - DUA DIA Reduction (Deprecated)", AuditReportAction.INFORMATIONAL, None,
    )
    DEPRECATED_LEAVE_PLAN_IN_REVIEW = LkPaymentAuditReportType(
        3, "Deprecated - Leave Plan In Review", AuditReportAction.SKIPPED, None,
    )
    DOR_FINEOS_NAME_MISMATCH = LkPaymentAuditReportType(
        4,
        "DOR FINEOS Name Mismatch",
        AuditReportAction.INFORMATIONAL,
        "dor_fineos_name_mismatch_details",
    )
    DUA_ADDITIONAL_INCOME = LkPaymentAuditReportType(
        5,
        "DUA Additional Income",
        AuditReportAction.INFORMATIONAL,
        "dua_additional_income_details",
    )
    DIA_ADDITIONAL_INCOME = LkPaymentAuditReportType(
        6,
        "DIA Additional Income",
        AuditReportAction.INFORMATIONAL,
        "dia_additional_income_details",
    )
    PAYMENT_DATE_MISMATCH = LkPaymentAuditReportType(
        7, "Payment Date Mismatch", AuditReportAction.REJECTED, "payment_date_mismatch_details",
    )
    EXCEEDS_26_WEEKS_TOTAL_LEAVE = LkPaymentAuditReportType(
        8,
        "Exceeds 26 weeks of total leave",
        AuditReportAction.INFORMATIONAL,
        "exceeds_26_weeks_total_leave_details",
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


class LkWithholdingType(Base):
    __tablename__ = "lk_withholding_type"
    withholding_type_id = Column(Integer, primary_key=True, autoincrement=True)
    withholding_type_description = Column(Text, nullable=False)

    def __init__(
        self, withholding_type_id, withholding_type_description,
    ):
        self.withholding_type_id = withholding_type_id
        self.withholding_type_description = withholding_type_description


class WithholdingType(LookupTable):
    model = LkWithholdingType
    column_names = (
        "withholding_type_id",
        "withholding_type_description",
    )

    FEDERAL = LkWithholdingType(1, "Federal Tax")
    STATE = LkWithholdingType(2, "State Tax")


class Pfml1099MMARSPayment(Base, TimestampMixin):
    __tablename__ = "pfml_1099_mmars_payment"
    pfml_1099_mmars_payment_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    pfml_1099_batch_id = Column(
        PostgreSQLUUID, ForeignKey("pfml_1099_batch.pfml_1099_batch_id"), index=True, nullable=False
    )
    mmars_payment_id = Column(
        PostgreSQLUUID,
        ForeignKey("mmars_payment_data.mmars_payment_data_id"),
        index=True,
        nullable=False,
    )
    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True, nullable=False
    )
    payment_amount = Column(Numeric, nullable=False)
    payment_date = Column(Date, nullable=False)

    mmars_payment_data = relationship(MmarsPaymentData)
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
    cancel_date = Column(Date, nullable=True)

    payment = relationship(Payment)
    claim = relationship(Claim)
    employee = relationship(Employee)


class Pfml1099Batch(Base, TimestampMixin):
    __tablename__ = "pfml_1099_batch"
    pfml_1099_batch_id = Column(PostgreSQLUUID, primary_key=True, nullable=False)
    tax_year = Column(Integer, nullable=False)
    batch_run_date = Column(Date, nullable=False)
    correction_ind = Column(Boolean, nullable=False)
    batch_status = Column(Text)


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
    withholding_type_id = Column(
        Integer, ForeignKey("lk_withholding_type.withholding_type_id"), index=True, nullable=False
    )

    payment = relationship(Payment)
    claim = relationship(Claim)
    employee = relationship(Employee)
    withholding_type = relationship(LkWithholdingType)


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


class Pfml1099RefundBackup(Base, TimestampMixin):
    __tablename__ = "pfml_1099_refund_backup"
    pfml_1099_refund_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    pfml_1099_batch_id = Column(PostgreSQLUUID, nullable=True)
    payment_id = Column(PostgreSQLUUID, nullable=True)
    employee_id = Column(PostgreSQLUUID, nullable=True)
    refund_amount = Column(Numeric, nullable=True)
    refund_date = Column(Date, nullable=True)


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
    account_number = Column(Text)
    c = Column(Text)
    i = Column(Text)
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
    s3_location = Column(Text, nullable=True)
    fineos_status = Column(Text, nullable=True, default="New")

    employee = relationship(Employee)


class Pfml1099Request(Base, TimestampMixin):
    __tablename__ = "pfml_1099_request"
    pfml_1099_request_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True, nullable=False
    )
    correction_ind = Column(Boolean, nullable=False)
    pfml_1099_batch_id = Column(
        PostgreSQLUUID, ForeignKey("pfml_1099_batch.pfml_1099_batch_id"), index=True, nullable=True
    )

    employee = relationship(Employee)


class LinkSplitPayment(Base, TimestampMixin):
    __tablename__ = "link_split_payment"
    payment_id = Column(PostgreSQLUUID, ForeignKey("payment.payment_id"), primary_key=True)
    related_payment_id = Column(PostgreSQLUUID, ForeignKey("payment.payment_id"), primary_key=True)

    payment = relationship(Payment, foreign_keys=[payment_id])
    related_payment = cast(
        "Optional[Payment]", relationship(Payment, foreign_keys=[related_payment_id])
    )


#### Writeback Status Mapping Configuration
# This config helps us map the following:
# AuditReportType -> Reject Notes -> Writeback transaction status
class AuditReportDetailGroup:
    reject_notes_str: str
    inbound_reject_notes_str: str

    writeback_transaction_status: LkFineosWritebackTransactionStatus
    audit_report_type: Optional[LkPaymentAuditReportType]

    def __init__(
        self,
        reject_notes_str: str,
        writeback_transaction_status: LkFineosWritebackTransactionStatus,
        inbound_reject_notes_override_str: Optional[str] = None,
        audit_report_type: Optional[LkPaymentAuditReportType] = None,
    ):
        self.reject_notes_str = reject_notes_str
        self.writeback_transaction_status = writeback_transaction_status
        self.inbound_reject_notes_str = (
            inbound_reject_notes_override_str
            if inbound_reject_notes_override_str
            else self.reject_notes_str
        )
        self.audit_report_type = audit_report_type


# All scenarios where the payment
# would be marked as rejected
AUDIT_REJECT_DETAIL_GROUPS = [
    AuditReportDetailGroup(
        reject_notes_str=PaymentAuditReportType.DUA_ADDITIONAL_INCOME.payment_audit_report_type_description,
        writeback_transaction_status=FineosWritebackTransactionStatus.DUA_ADDITIONAL_INCOME,
        audit_report_type=PaymentAuditReportType.DUA_ADDITIONAL_INCOME,
    ),
    AuditReportDetailGroup(
        reject_notes_str=PaymentAuditReportType.DIA_ADDITIONAL_INCOME.payment_audit_report_type_description,
        writeback_transaction_status=FineosWritebackTransactionStatus.DIA_ADDITIONAL_INCOME,
        audit_report_type=PaymentAuditReportType.DIA_ADDITIONAL_INCOME,
    ),
    AuditReportDetailGroup(
        reject_notes_str=PaymentAuditReportType.DOR_FINEOS_NAME_MISMATCH.payment_audit_report_type_description,
        writeback_transaction_status=FineosWritebackTransactionStatus.NAME_MISMATCH,
        audit_report_type=PaymentAuditReportType.DOR_FINEOS_NAME_MISMATCH,
        inbound_reject_notes_override_str="Name mismatch",  # Rather than the "DOR FINEOS Name Mismatch" that we send
    ),
    AuditReportDetailGroup(
        reject_notes_str=PaymentAuditReportType.EXCEEDS_26_WEEKS_TOTAL_LEAVE.payment_audit_report_type_description,
        writeback_transaction_status=FineosWritebackTransactionStatus.LEAVE_DURATION_MAX_EXCEEDED,
        audit_report_type=PaymentAuditReportType.EXCEEDS_26_WEEKS_TOTAL_LEAVE,
    ),
    AuditReportDetailGroup(
        reject_notes_str=PaymentAuditReportType.PAYMENT_DATE_MISMATCH.payment_audit_report_type_description,
        writeback_transaction_status=FineosWritebackTransactionStatus.LEAVE_DATES_CHANGE,
        audit_report_type=PaymentAuditReportType.PAYMENT_DATE_MISMATCH,
    ),
    AuditReportDetailGroup(
        reject_notes_str="Self-Reported Additional Income",
        writeback_transaction_status=FineosWritebackTransactionStatus.SELF_REPORTED_ADDITIONAL_INCOME,
        audit_report_type=None,
    ),
    AuditReportDetailGroup(
        reject_notes_str="Waiting Week",
        writeback_transaction_status=FineosWritebackTransactionStatus.WAITING_WEEK,
        audit_report_type=None,
    ),
    AuditReportDetailGroup(
        reject_notes_str="InvalidPayment PaidDate",
        writeback_transaction_status=FineosWritebackTransactionStatus.ALREADY_PAID_FOR_DATES,
        audit_report_type=None,
    ),
    AuditReportDetailGroup(
        reject_notes_str="Leave Dates Change",
        writeback_transaction_status=FineosWritebackTransactionStatus.LEAVE_DATES_CHANGE,
        audit_report_type=None,
    ),
    AuditReportDetailGroup(
        reject_notes_str="Under or Over payments(Adhocs needed)",
        writeback_transaction_status=FineosWritebackTransactionStatus.UNDER_OR_OVERPAY_ADJUSTMENT,
        audit_report_type=None,
    ),
    # TODO: Potentially remove below? Check with audit team if the new automation requires
    # that we handle these cases in the audit report anymore.
    AuditReportDetailGroup(
        reject_notes_str="Exempt Employer",
        writeback_transaction_status=FineosWritebackTransactionStatus.EXEMPT_EMPLOYER,
        audit_report_type=None,
    ),
    AuditReportDetailGroup(
        reject_notes_str="Weekly benefit amount exceeds $850",
        writeback_transaction_status=FineosWritebackTransactionStatus.WEEKLY_BENEFITS_AMOUNT_EXCEEDS_850,
        audit_report_type=None,
    ),
    # Fallback value
    AuditReportDetailGroup(
        reject_notes_str="Other",
        writeback_transaction_status=FineosWritebackTransactionStatus.FAILED_MANUAL_VALIDATION,
        audit_report_type=None,
    ),
]

AUDIT_REJECT_NOTE_TO_WRITEBACK_TRANSACTION_STATUS = {
    group.inbound_reject_notes_str: group.writeback_transaction_status
    for group in AUDIT_REJECT_DETAIL_GROUPS
}

# We currently don't have any scenarios for skipped
# records that get specific audit statuses
# but creating to show the pattern
AUDIT_SKIPPED_DETAIL_GROUPS = [
    # TODO: Potentially remove below? Check with audit team if the new automation requires
    # that we handle these cases in the audit report anymore.
    AuditReportDetailGroup(
        reject_notes_str="Leave Plan In Review",
        writeback_transaction_status=FineosWritebackTransactionStatus.LEAVE_IN_REVIEW,
        audit_report_type=None,
    ),
    # Fallback Value
    AuditReportDetailGroup(
        reject_notes_str="Other",
        writeback_transaction_status=FineosWritebackTransactionStatus.PENDING_PAYMENT_AUDIT,
        audit_report_type=None,
    ),
]
AUDIT_SKIPPED_NOTE_TO_WRITEBACK_TRANSACTION_STATUS = {
    group.inbound_reject_notes_str: group.writeback_transaction_status
    for group in AUDIT_SKIPPED_DETAIL_GROUPS
}


def sync_lookup_tables(db_session):
    FineosWritebackTransactionStatus.sync_to_database(db_session)
    PaymentAuditReportType.sync_to_database(db_session)
    WithholdingType.sync_to_database(db_session)

    db_session.commit()
