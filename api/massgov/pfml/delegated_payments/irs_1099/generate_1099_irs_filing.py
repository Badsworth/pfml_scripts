import decimal
import os
import uuid
from typing import Any, List, Tuple

from sqlalchemy.sql.sqltypes import Boolean

import massgov.pfml.delegated_payments.delegated_config as paymentConfig
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType, TaxIdentifier
from massgov.pfml.db.models.payments import Pfml1099
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)

total_b_record = 0


class Constants:
    T_REC_TYPE = "T"
    A_REC_TYPE = "A"
    B_REC_TYPE = "B"
    C_REC_TYPE = "C"
    K_REC_TYPE = "K"
    F_REC_TYPE = "F"
    # Will be 'P' for previous year and blank for current year
    PREV_YR_IND = ""
    TAX_YEAR = 2021
    # TRANSMITTER INFO
    TX_CTL_NO = "08025"
    TX_NAME = "COMMONWEALTH OF MASSACHUSETTS"
    # COMPANY DETAILS
    COM_NM = "COMMONWEALTH OF MASSACHUSETTS"
    COM_ADDR = "ONE ASHBURTON PL ROOM 901"
    COM_CTY = "BOSTON"
    COM_ST = "MA"
    COM_ZIP_CD = "02108"
    # CONTACT DETAILS
    CONT_NM = "JESSICA A COGSWELL"
    CONT_PH = "6179732323"
    CONT_EMAIL = "jessica.cogswell@mass.gov"
    # PAYER INFO
    PAYER_TIN = "046002284"
    PAYER_LNAME = "COMM"
    PYR_PHONE = 6179732323
    PAYER_ACCT_NUMBER = ""
    PAYER_OFFICE_CD = ""
    VEN_IND = "I"
    RETURN_TYPE = "F"
    # For unemployment compensation, amt_cd is 1,
    # Might add 4 for fed tax later
    AMT_CD = 1
    TA_IND = 0
    TOT_A_REC = 1
    # If COMBINED_ST_FED_IND is set to 1, then this is 25 else blank
    COMBINED_ST_FED_CD = 25
    # Send as 1 in test file and if approved, send 1 else blank
    COMBINED_ST_FED_IND = 1
    SECOND_TIN_NOTICE = ""
    TIN_TYPE = 2
    # Check this in future.For now, it is blank indicating current year
    TAX_YR_OF_REFUND = ""
    # Will be set to 'T' for test file only
    TST_FILE_IND = ""
    BLANK_SPACE = ""
    FILE_NAME = "1099.ORG"
    G1099_FILENAME_FORMAT = f"%Y-%m-%d-%H-%M-%S-{FILE_NAME}"
    ZERO = 0
    AMT_CD_1 = 0


class Generate1099IRSfilingStep(Step):
    def run_step(self) -> None:
        self._generate_1099_irs_filing()

    def _generate_1099_irs_filing(self) -> None:
        logger.info("1099 Documents - Generate 1099.org file to be transmitted to IRS")

        recent_batch_id = pfml_1099_util.get_current_1099_batch(self.db_session)
        if recent_batch_id is None:
            logger.error("No current batch exists.")
        else:
            try:
                logger.info("recent_batch_id %s", recent_batch_id.pfml_1099_batch_id)
                pfml_1099 = list(
                    self.db_session.query(Pfml1099).filter(
                        Pfml1099.pfml_1099_batch_id == recent_batch_id.pfml_1099_batch_id
                    )
                )
            except Exception:
                logger.exception("Error accessing 1099 data")
                raise
            self.total_b_record = len(pfml_1099)
            logger.info("Total b records are, %s", self.total_b_record)
            b_template = self._create_b_template()
            b_entries = self._load_b_rec_data(b_template, pfml_1099)
            t_template = self._create_t_template()
            t_entries = self._load_t_rec_data(t_template)
            a_template = self._create_a_template()
            a_entries = self._load_a_rec_data(a_template)
            entries = t_entries + a_entries
            for b_records in b_entries:
                entries = entries + b_records
            self._create_irs_file(entries)
            self.db_session.commit()

    def _create_t_template(self) -> str:
        temp = (
            "{T_REC_TYPE:<1}{TAX_YEAR:<4}{PREV_YR_IND:<1}{TX_TIN:<9}{TX_CTL_NO:<5}{B7:<7}"
            "{TST_FILE_IND:<1}{FOR_IND:<1}{TX_NAME:<80}{COMP_NAME:<80}{COMP_ADDR:<40}"
            "{COMP_CTY:<40}{COMP_ST:<2}{COMP_ZIP_CD:0<9}{B15:<15}{TOT_B_REC:08}"
            "{CONT_NM:<40}{CONT_PH:<15}{CONT_EMAIL:<50}{B91:<91}{SEQ_NO:08}{B10:<10}"
            "{VEN_IND:<1}{VEN_INFO:<232}\n"
        )
        logger.debug("Template string is %s", temp)
        return temp

    def _create_a_template(self) -> str:
        temp = (
            "{A_REC_TYPE:<1}{TAX_YEAR:<4}{CSF_IND:<1}{B5:<5}{PYR_TIN:<9}"
            "{PYR_NM_CTL:<4}{LAST_FILING_IND:<1}{TYPE_RET:<2}{AMT_CD:016}{B8:<8}"
            "{FE_IND:<1}{PYR_NM:<80}{TA_IND:<1}{PYR_ADDR:<40}{PYR_CTY:<40}"
            "{PYR_ST:<2}{PYR_ZC:0<9}{PYR_PHONE:<15}{B260:<260}{SEQ_NO:08}{B243:<243}\n"
        )
        logger.debug("Template string is %s", temp)
        return temp

    def _create_b_template(self) -> str:
        temp = (
            "{B_REC_TYPE:<1}{TAX_YEAR:<4}{CORRECTION_IND:<1}{PAYEE_NAME_CTL:<4}"
            "{PAYEE_TIN_TYPE:<1}{PAYEE_TIN:<9}{PAYER_ACCT_NUMBER:<20}{PAYER_OFFICE_CD:<4}"
            "{B10:<10}{AMT_CD_1:0>12}{AMT_CD_2:0>12}{AMT_CD_3:0>12}{AMT_CD_4:0>12}"
            "{AMT_CD_5:0>12}{AMT_CD_6:0>12}{AMT_CD_7:0>12}{AMT_CD_8:0>12}{AMT_CD_9:0>12}"
            "{AMT_CD_A:0>12}{AMT_CD_B:0>12}{AMT_CD_C:0>12}{AMT_CD_D:0>12}{AMT_CD_E:0>12}"
            "{AMT_CD_F:0>12}{AMT_CD_G:0>12}"
            "{FE_IND:<1}{PAYEE_NM1:<40}{PAYEE_NM2:<40}{B40:<40}{PAYEE_ADDRESS:<40}"
            "{B40_1:<40}{PAYEE_CTY:<40}{PAYEE_ST:<2}{PAYEE_ZC:0<9}{B1:<1}"
            "{SEQ_NO:0>8}{B36:<36}{SEC_TIN_NOTICE:<1}{B2:<2}{TRADE_BUS_IND:<1}"
            "{TAX_YR_OF_REFUND:<4}{B111:<111}{SP_DATA_ENTRIES:<60}{ST_TAX:0>12}"
            "{LOCAL_TAX:0>12}{CSF_CD:<2}{B2_1:<2}\n"
        )
        logger.debug("Template string is %s", temp)
        return temp

    def _create_irs_file(self, all_records: str) -> None:

        logger.info("creating irs file")
        s3_config = paymentConfig.get_s3_config()
        now = payments_util.get_now()
        report_path = s3_config.pfml_error_reports_archive_path
        dfml_sharepoint_outgoing_path = s3_config.dfml_report_outbound_path
        source_path = payments_util.build_archive_path(
            report_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            now.strftime(Constants.G1099_FILENAME_FORMAT),
            now,
        )
        with file_util.write_file(source_path) as irs_file:
            irs_file.write(all_records)
        outgoing_s3_path = os.path.join(dfml_sharepoint_outgoing_path, Constants.FILE_NAME)
        file_util.copy_file(source_path, outgoing_s3_path)
        reference_file = ReferenceFile(
            file_location=str(source_path),
            reference_file_type_id=ReferenceFileType.IRS_1099_ORIG.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
        self.db_session.add(reference_file)

    def _load_t_rec_data(self, template_str: str) -> str:

        t_dict = dict(
            T_REC_TYPE=Constants.T_REC_TYPE,
            PREV_YR_IND=Constants.PREV_YR_IND,
            TAX_YEAR=Constants.TAX_YEAR,
            TX_TIN=Constants.PAYER_TIN,
            TX_CTL_NO=Constants.TX_CTL_NO,
            B7=Constants.BLANK_SPACE,
            TST_FILE_IND=Constants.TST_FILE_IND,
            FOR_IND=Constants.BLANK_SPACE,
            TX_NAME=Constants.TX_NAME,
            COMP_NAME=Constants.COM_NM,
            COMP_ADDR=Constants.COM_ADDR,
            COMP_CTY=Constants.COM_CTY,
            COMP_ST=Constants.COM_ST,
            COMP_ZIP_CD=Constants.COM_ZIP_CD,
            B15=Constants.BLANK_SPACE,
            TOT_B_REC=self.total_b_record,
            CONT_NM=Constants.CONT_NM,
            CONT_PH=Constants.CONT_PH,
            CONT_EMAIL=Constants.CONT_EMAIL,
            B91=Constants.BLANK_SPACE,
            SEQ_NO=1,
            B10=Constants.BLANK_SPACE,
            VEN_IND=Constants.VEN_IND,
            VEN_INFO=Constants.BLANK_SPACE,
        )
        t_record = template_str.format_map(t_dict)
        return t_record

    def _load_a_rec_data(self, template_str: str) -> str:

        a_dict = dict(
            A_REC_TYPE=Constants.A_REC_TYPE,
            TAX_YEAR=Constants.TAX_YEAR,
            CSF_IND=Constants.COMBINED_ST_FED_IND,
            B5=Constants.BLANK_SPACE,
            PYR_TIN=Constants.PAYER_TIN,
            PYR_NM_CTL=Constants.PAYER_LNAME,
            LAST_FILING_IND=Constants.BLANK_SPACE,
            TYPE_RET=Constants.RETURN_TYPE,
            AMT_CD=Constants.AMT_CD,
            B8=Constants.BLANK_SPACE,
            FE_IND=Constants.BLANK_SPACE,
            PYR_NM=Constants.COM_NM,
            TA_IND=Constants.TA_IND,
            PYR_ADDR=Constants.COM_ADDR,
            PYR_CTY=Constants.COM_CTY,
            PYR_ST=Constants.COM_ST,
            PYR_ZC=Constants.COM_ZIP_CD,
            PYR_PHONE=Constants.PYR_PHONE,
            B260=Constants.BLANK_SPACE,
            SEQ_NO=2,
            B243=Constants.BLANK_SPACE,
        )
        a_record = template_str.format_map(a_dict)
        return a_record

    def _load_b_rec_data(self, template_str: str, tax_data: List[Any]) -> List[str]:
        b_dict_list = []
        b_seq = 3
        for records in tax_data:
            b_dict = dict(
                B_REC_TYPE=Constants.B_REC_TYPE,
                TAX_YEAR=Constants.TAX_YEAR,
                CORRECTION_IND=_get_correction_ind(records.correction_ind),
                PAYEE_NAME_CTL=_get_name_ctl(records.last_name),
                PAYEE_TIN_TYPE=Constants.TIN_TYPE,
                PAYEE_TIN=_get_tax_id(self.db_session, records.tax_identifier_id),
                PAYER_ACCT_NUMBER=Constants.PAYER_ACCT_NUMBER,
                PAYER_OFFICE_CD=Constants.PAYER_OFFICE_CD,
                B10=Constants.BLANK_SPACE,
                AMT_CD_1=_format_amount_fields(records.gross_payments),
                AMT_CD_2=Constants.AMT_CD_1,
                AMT_CD_3=Constants.AMT_CD_1,
                AMT_CD_4=Constants.AMT_CD_1,
                AMT_CD_5=Constants.AMT_CD_1,
                AMT_CD_6=Constants.AMT_CD_1,
                AMT_CD_7=Constants.AMT_CD_1,
                AMT_CD_8=Constants.AMT_CD_1,
                AMT_CD_9=Constants.AMT_CD_1,
                AMT_CD_A=Constants.AMT_CD_1,
                AMT_CD_B=Constants.AMT_CD_1,
                AMT_CD_C=Constants.AMT_CD_1,
                AMT_CD_D=Constants.AMT_CD_1,
                AMT_CD_E=Constants.AMT_CD_1,
                AMT_CD_F=Constants.AMT_CD_1,
                AMT_CD_G=Constants.AMT_CD_1,
                FE_IND=Constants.BLANK_SPACE,
                PAYEE_NM1=_get_full_name(records.first_name, records.last_name, "PAYEE_NM1"),
                PAYEE_NM2=_get_full_name(records.first_name, records.last_name, "PAYEE_NM2"),
                B40=Constants.BLANK_SPACE,
                PAYEE_ADDRESS=records.address_line_1.upper(),
                B40_1=Constants.BLANK_SPACE,
                PAYEE_CTY=records.city.upper(),
                PAYEE_ST=records.state.upper(),
                PAYEE_ZC=records.zip,
                B1=Constants.BLANK_SPACE,
                SEQ_NO=b_seq,
                B36=Constants.BLANK_SPACE,
                SEC_TIN_NOTICE=Constants.BLANK_SPACE,
                B2=Constants.BLANK_SPACE,
                TRADE_BUS_IND=Constants.BLANK_SPACE,
                TAX_YR_OF_REFUND=Constants.BLANK_SPACE,
                B111=Constants.BLANK_SPACE,
                SP_DATA_ENTRIES=Constants.BLANK_SPACE,
                ST_TAX=_format_amount_fields(records.state_tax_withholdings),
                LOCAL_TAX=_format_amount_fields(records.federal_tax_withholdings),
                CSF_CD=Constants.COMBINED_ST_FED_CD,
                B2_1=Constants.BLANK_SPACE,
            )
            b_record = template_str.format_map(b_dict)
            # logger.info(b_record)
            b_seq = b_seq + 1
            b_dict_list.append(b_record)
        return b_dict_list


def _get_correction_ind(correction_ind: Boolean) -> str:

    if not correction_ind:
        return Constants.BLANK_SPACE
    else:
        # TODO find which correction type to send and how to determine
        # G (1 correction) or C(2 correction)
        return "G"


def _get_tax_id(db_session: Any, tax_id_str: str) -> str:
    logger.debug("Incoming tax uuid is, %s", tax_id_str)
    try:
        tax_id = (
            db_session.query(TaxIdentifier)
            .filter(TaxIdentifier.tax_identifier_id == tax_id_str)
            .one_or_none()
        )
        logger.debug("tax id is %s", tax_id.tax_identifier)
        return tax_id.tax_identifier

    except Exception:
        logger.exception("Error accessing 1099 data")
        raise


def _get_full_name(fname: str, lname: str, field_name: str) -> str:
    full_name = lname + Constants.BLANK_SPACE + fname
    name_length = len(full_name)
    if name_length <= 40:
        if field_name == "PAYEE_NM1":
            return full_name.upper()
        else:
            return Constants.BLANK_SPACE
    else:
        first_forty_chars = full_name[:40]
        last_chars = full_name[40:name_length]
        if field_name == "PAYEE_NM1":
            return first_forty_chars.upper()
        else:
            return last_chars.upper()


def _get_name_ctl(lname: str) -> str:
    last_name_four = ""
    if lname.find("-") != -1:
        last_name = lname.split("-")[0]
    elif lname.find(" ") != -1:
        last_name_list = lname.split(" ")
        name_length = len(last_name_list)
        if name_length == 2:
            last_name = last_name_list[1]
        else:
            last_name = last_name_list[0].rstrip() + last_name_list[1]
    else:
        last_name = lname
    logger.info("Last name 4 chars is %s", last_name[0:4])
    last_name_four = last_name[0:4].upper()
    return last_name_four


def _format_amount_fields(amt: decimal.Decimal) -> str:

    amount = str(amt).split(".")
    print(amount)
    dollars = amount[0]
    if len(amount) == 2:
        cents = amount[1]
        if len(cents) == 2:
            cents = cents
        elif len(cents) == 1:
            cents = cents + "0"
    else:
        cents = "00"
    format_amt = dollars + cents
    return format_amt


def _get_totals(tax_data: List[Any]) -> Tuple:
    ctl_total = decimal.Decimal(0.0)
    st_tax = decimal.Decimal(0.0)
    fed_tax = decimal.Decimal(0.0)

    for records in tax_data:
        ctl_total += records.gross_payments
        st_tax += records.state_tax_withholdings
        fed_tax += records.federal_tax_withholdings
    return (
        _format_amount_fields(ctl_total),
        _format_amount_fields(st_tax),
        _format_amount_fields(fed_tax),
    )
