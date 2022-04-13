import decimal
import enum
import os
import re
import uuid
from typing import Any, List, Tuple

import massgov.pfml.delegated_payments.delegated_config as paymentConfig
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.util.datetime import get_now_us_eastern

logger = massgov.pfml.util.logging.get_logger(__name__)


class Constants:
    T_REC_TYPE = "T"
    A_REC_TYPE = "A"
    B_REC_TYPE = "B"
    C_REC_TYPE = "C"
    K_REC_TYPE = "K"
    F_REC_TYPE = "F"
    # Will be 'P' for previous year and blank for current year
    PREV_YR_IND = ""
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
    FILE_NAME = "1099.txt"
    G1099_FILENAME_FORMAT = f"%Y-%m-%d-%H-%M-%S-{FILE_NAME}"
    ZERO = 0
    AMT_CD_1 = 0


class Generate1099IRSfilingStep(Step):
    class Metrics(str, enum.Enum):
        IRS_FILE_1099_COUNT = "irs_file_1099_count"
        IRS_FILE_1099_CORRECTED_COUNT = "irs_file_1099_corrected_count"
        IRS_FILE_1099_C_CORRECTION_COUNT = "irs_file_1099_c_correction_count"
        IRS_FILE_1099_G_CORRECTION_COUNT = "irs_file_1099_g_correction_count"

    total_b_record = 0
    total_a_record = 0
    seq_number = 1
    total_b_correction_record = 0

    def run_step(self) -> None:
        self._generate_1099_irs_filing()

    def _generate_1099_irs_filing(self) -> None:
        logger.info("1099 Documents - Generate 1099.org file to be transmitted to IRS")

        t_template = self._create_t_template()
        t_entries = self._load_t_rec_data(t_template)
        entries = t_entries
        if pfml_1099_util.is_correction_submission():
            pfml_1099_corrected = pfml_1099_util.get_1099_corrected_records_to_file(self.db_session)
            if len(pfml_1099_corrected) > 0:
                self.total_b_correction_record = len(pfml_1099_corrected)
                logger.info("Total b records are, %s", self.total_b_correction_record)

                g_corrected_list, c_corrected_list, batch_id = self.process_correction_types(
                    pfml_1099_corrected
                )

                if len(g_corrected_list) > 0:
                    entries = self._create_correction_entries(entries, g_corrected_list, "G")
                if len(c_corrected_list) > 0:
                    entries = self._create_correction_entries(entries, c_corrected_list, "C")
                f_template = self._create_f_template()
                f_entries = self._load_f_rec_data(f_template)
                entries += f_entries
                logger.info("Completed irs file data mapping")
                self._create_irs_file(entries)
                pfml_1099_util.update_submission_date(self.db_session, batch_id)
                self.db_session.commit()
        else:

            pfml_1099 = pfml_1099_util.get_1099_records_to_file(self.db_session)
            if len(pfml_1099) > 0:
                if pfml_1099_util.is_test_file() == "T":
                    pfml_1099 = pfml_1099[:11]
                self.total_b_record = len(pfml_1099)
                logger.info("Total b records are, %s", self.total_b_record)
                a_template = self._create_a_template()
                a_entries = self._load_a_rec_data(a_template)
                entries += a_entries
                b_template = self._create_b_template()
                b_entries = self._load_b_rec_data(b_template, pfml_1099)
                for b_records in b_entries:
                    entries = entries + b_records
                c_template = self._create_c_template()
                ctl_total, st_tax, fed_tax = self._get_totals(pfml_1099)
                c_entries = self._load_c_rec_data(c_template, ctl_total)
                k_template = self._create_k_template()
                k_entries = self._load_k_rec_data(k_template, ctl_total, st_tax, fed_tax)
                entries += c_entries + k_entries

                f_template = self._create_f_template()
                f_entries = self._load_f_rec_data(f_template)
                entries += f_entries
                logger.info("Completed irs file data mapping")
                self._create_irs_file(entries)
                pfml_1099_util.update_submission_date(
                    self.db_session, pfml_1099[0].pfml_1099_batch_id
                )
                self.db_session.commit()

    def _create_correction_entries(
        self, t_entries: str, corr_list: List[Any], corr_ind: str
    ) -> str:
        a_template = self._create_a_template()
        a_entries = self._load_a_rec_data(a_template)
        entries = t_entries + a_entries
        b_template = self._create_b_template()
        b_entries = self._load_corrected_b_rec_data(b_template, corr_list, corr_ind)
        for b_records in b_entries:
            entries = entries + b_records
        c_template = self._create_c_template()
        ctl_total, st_tax, fed_tax = self._get_correction_totals(corr_list, corr_ind)
        c_entries = self._load_c_rec_data(c_template, ctl_total)
        k_template = self._create_k_template()
        k_entries = self._load_k_rec_data(k_template, ctl_total, st_tax, fed_tax)
        entries = entries + c_entries + k_entries
        return entries

    def _create_t_template(self) -> str:
        temp = (
            "{T_REC_TYPE:<1}{TAX_YEAR:<4}{PREV_YR_IND:<1}{TX_TIN:<9}{TX_CTL_NO:<5}{B7:<7}"
            "{TST_FILE_IND:<1}{FOR_IND:<1}{TX_NAME:<80}{COMP_NAME:<80}{COMP_ADDR:<40}"
            "{COMP_CTY:<40}{COMP_ST:<2}{COMP_ZIP_CD:0<9}{B15:<15}{TOT_B_REC:08}"
            "{CONT_NM:<40}{CONT_PH:<15}{CONT_EMAIL:<50}{B91:<91}{SEQ_NO:08}{B10:<10}"
            "{VEN_IND:<1}{VEN_INFO:<230}\r\n"
        )
        return temp

    def _create_a_template(self) -> str:
        temp = (
            "{A_REC_TYPE:<1}{TAX_YEAR:<4}{CSF_IND:<1}{B5:<5}{PYR_TIN:<9}"
            "{PYR_NM_CTL:<4}{LAST_FILING_IND:<1}{TYPE_RET:<2}{AMT_CD:<18}{B6:<6}"
            "{FE_IND:<1}{PYR_NM:<80}{TA_IND:<1}{PYR_ADDR:<40}{PYR_CTY:<40}"
            "{PYR_ST:<2}{PYR_ZC:0<9}{PYR_PHONE:<15}{B260:<260}{SEQ_NO:08}{B241:<241}\r\n"
        )
        return temp

    def _create_b_template(self) -> str:
        temp = (
            "{B_REC_TYPE:<1}{TAX_YEAR:<4}{CORRECTION_IND:<1}{PAYEE_NAME_CTL:<4}"
            "{PAYEE_TIN_TYPE:<1}{PAYEE_TIN:<9}{PAYER_ACCT_NUMBER:<20}{PAYER_OFFICE_CD:<4}"
            "{B10:<10}{AMT_CD_1:0>12}{AMT_CD_2:0>12}{AMT_CD_3:0>12}{AMT_CD_4:0>12}"
            "{AMT_CD_5:0>12}{AMT_CD_6:0>12}{AMT_CD_7:0>12}{AMT_CD_8:0>12}{AMT_CD_9:0>12}"
            "{AMT_CD_A:0>12}{AMT_CD_B:0>12}{AMT_CD_C:0>12}{AMT_CD_D:0>12}{AMT_CD_E:0>12}"
            "{AMT_CD_F:0>12}{AMT_CD_G:0>12}{AMT_CD_H:0>12}{AMT_CD_J:0>12}"
            "{B16:<16}{FE_IND:<1}{PAYEE_NM1:<40}{PAYEE_NM2:<40}{PAYEE_ADDRESS:<40}"
            "{B40_1:<40}{PAYEE_CTY:<40}{PAYEE_ST:<2}{PAYEE_ZC:0<9}{B1:<1}"
            "{SEQ_NO:0>8}{B36:<36}{SEC_TIN_NOTICE:<1}{B2:<2}{TRADE_BUS_IND:<1}"
            "{TAX_YR_OF_REFUND:<4}{B111:<111}{SP_DATA_ENTRIES:<60}{ST_TAX:0>12}"
            "{LOCAL_TAX:0>12}{CSF_CD:<2}\r\n"
        )
        return temp

    def _create_c_template(self) -> str:
        temp = (
            "{C_REC_TYPE:<1}{TOT_B_REC:0>8}{B6:<6}{CTL_TOTAL_1:0>18}{CTL_TOTAL:0>306}{B160:<160}{SEQ_NO:08}"
            "{B241:<241}\r\n"
        )
        return temp

    def _create_k_template(self) -> str:
        temp = (
            "{K_REC_TYPE:<1}{TOT_B_REC:0>8}{B6:<6}{CTL_TOTAL_1:0>18}{CTL_TOTAL:0>306}{B160:<160}{SEQ_NO:08}"
            "{B199:<199}{ST_TAX:0>18}{FED_TAX:0>18}{B4:<4}{CSF_CD:<2}\r\n"
        )
        return temp

    def _create_f_template(self) -> str:
        temp = (
            "{F_REC_TYPE:<1}{TOT_A_REC:0>8}{ZERO_21:0<21}{B19:<19}{TOT_B_REC:0>8}{B442:<442}"
            "{SEQ_NO:08}{B241:<241}\r\n"
        )
        return temp

    def _create_irs_file(self, all_records: str) -> None:

        logger.info("creating irs file")
        s3_config = paymentConfig.get_s3_config()
        now = get_now_us_eastern()
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
            reference_file_type_id=ReferenceFileType.IRS_1099_FILE.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
        self.db_session.add(reference_file)

    def _load_t_rec_data(self, template_str: str) -> str:

        t_dict = dict(
            T_REC_TYPE=Constants.T_REC_TYPE,
            PREV_YR_IND=Constants.PREV_YR_IND,
            TAX_YEAR=pfml_1099_util.get_tax_year(),
            TX_TIN=Constants.PAYER_TIN,
            TX_CTL_NO=Constants.TX_CTL_NO,
            B7=Constants.BLANK_SPACE,
            TST_FILE_IND=pfml_1099_util.is_test_file(),
            FOR_IND=Constants.BLANK_SPACE,
            TX_NAME=Constants.TX_NAME,
            COMP_NAME=Constants.COM_NM,
            COMP_ADDR=Constants.COM_ADDR,
            COMP_CTY=Constants.COM_CTY,
            COMP_ST=Constants.COM_ST,
            COMP_ZIP_CD=Constants.COM_ZIP_CD,
            B15=Constants.BLANK_SPACE,
            B16=Constants.BLANK_SPACE,
            TOT_B_REC=self.total_b_record,
            CONT_NM=Constants.CONT_NM,
            CONT_PH=Constants.CONT_PH,
            CONT_EMAIL=Constants.CONT_EMAIL,
            B91=Constants.BLANK_SPACE,
            SEQ_NO=self.seq_number,
            B10=Constants.BLANK_SPACE,
            VEN_IND=Constants.VEN_IND,
            VEN_INFO=Constants.BLANK_SPACE,
        )
        t_record = template_str.format_map(t_dict)
        return t_record

    def _load_a_rec_data(self, template_str: str) -> str:
        a_seq = self.seq_number + 1
        self.total_a_record += 1
        a_dict = dict(
            A_REC_TYPE=Constants.A_REC_TYPE,
            TAX_YEAR=pfml_1099_util.get_tax_year(),
            CSF_IND=Constants.COMBINED_ST_FED_IND,
            B5=Constants.BLANK_SPACE,
            PYR_TIN=Constants.PAYER_TIN,
            PYR_NM_CTL=Constants.PAYER_LNAME,
            LAST_FILING_IND=Constants.BLANK_SPACE,
            TYPE_RET=Constants.RETURN_TYPE,
            AMT_CD=Constants.AMT_CD,
            B6=Constants.BLANK_SPACE,
            FE_IND=Constants.BLANK_SPACE,
            PYR_NM=Constants.COM_NM,
            TA_IND=Constants.TA_IND,
            PYR_ADDR=Constants.COM_ADDR,
            PYR_CTY=Constants.COM_CTY,
            PYR_ST=Constants.COM_ST,
            PYR_ZC=Constants.COM_ZIP_CD,
            PYR_PHONE=Constants.PYR_PHONE,
            B260=Constants.BLANK_SPACE,
            SEQ_NO=a_seq,
            B241=Constants.BLANK_SPACE,
        )
        a_record = template_str.format_map(a_dict)
        self.seq_number = self.seq_number + 1
        return a_record

    def _load_corrected_b_rec_data(
        self, template_str: str, corrected_tax_list: List[Any], correction_type: str
    ) -> List[str]:
        b_dict_list = []
        b_seq = self.seq_number + 1
        logger.info("B sequence starts at %s", b_seq)
        for item in corrected_tax_list:
            self.increment(self.Metrics.IRS_FILE_1099_CORRECTED_COUNT)

            if correction_type == "G" and item["correction_type"] == "C":
                amount = decimal.Decimal(0.0)
            else:
                amount = item["record"].gross_payments
            b_dict = dict(
                B_REC_TYPE=Constants.B_REC_TYPE,
                TAX_YEAR=item["record"].tax_year,
                CORRECTION_IND=correction_type,
                PAYEE_NAME_CTL=self._get_name_ctl(item["record"].last_name),
                PAYEE_TIN_TYPE=Constants.TIN_TYPE,
                PAYEE_TIN=pfml_1099_util.get_tax_id(
                    self.db_session, item["record"].tax_identifier_id
                ),
                PAYER_ACCT_NUMBER=Constants.PAYER_ACCT_NUMBER,
                PAYER_OFFICE_CD=Constants.PAYER_OFFICE_CD,
                B10=Constants.BLANK_SPACE,
                AMT_CD_1=self._format_amount_fields(amount),
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
                AMT_CD_H=Constants.AMT_CD_1,
                AMT_CD_J=Constants.AMT_CD_1,
                B16=Constants.BLANK_SPACE,
                FE_IND=Constants.BLANK_SPACE,
                PAYEE_NM1=self._get_full_name(
                    item["record"].first_name, item["record"].last_name, "PAYEE_NM1"
                ),
                PAYEE_NM2=self._get_full_name(
                    item["record"].first_name, item["record"].last_name, "PAYEE_NM2"
                ),
                PAYEE_ADDRESS=item["record"].address_line_1.upper(),
                B40_1=Constants.BLANK_SPACE,
                PAYEE_CTY=item["record"].city.upper(),
                PAYEE_ST=item["record"].state.upper(),
                PAYEE_ZC=self._get_zip(item["record"].zip),
                B1=Constants.BLANK_SPACE,
                SEQ_NO=b_seq,
                B36=Constants.BLANK_SPACE,
                SEC_TIN_NOTICE=Constants.BLANK_SPACE,
                B2=Constants.BLANK_SPACE,
                TRADE_BUS_IND=Constants.BLANK_SPACE,
                TAX_YR_OF_REFUND=Constants.BLANK_SPACE,
                B111=Constants.BLANK_SPACE,
                SP_DATA_ENTRIES=Constants.BLANK_SPACE,
                ST_TAX=self._format_amount_fields(item["record"].state_tax_withholdings),
                LOCAL_TAX=Constants.BLANK_SPACE,
                CSF_CD=Constants.COMBINED_ST_FED_CD,
            )
            b_record = template_str.format_map(b_dict)
            b_seq = b_seq + 1
            b_dict_list.append(b_record)
            self.seq_number = b_seq
        return b_dict_list

    def _load_b_rec_data(self, template_str: str, tax_data: List[Any]) -> List[str]:
        b_dict_list = []
        b_seq = self.seq_number + 1
        logger.info("B sequence starts at %s", b_seq)
        for records in tax_data:
            self.increment(self.Metrics.IRS_FILE_1099_COUNT)
            b_dict = dict(
                B_REC_TYPE=Constants.B_REC_TYPE,
                TAX_YEAR=pfml_1099_util.get_tax_year(),
                CORRECTION_IND=Constants.BLANK_SPACE,
                PAYEE_NAME_CTL=self._get_name_ctl(records.last_name),
                PAYEE_TIN_TYPE=Constants.TIN_TYPE,
                PAYEE_TIN=pfml_1099_util.get_tax_id(self.db_session, records.tax_identifier_id),
                PAYER_ACCT_NUMBER=Constants.PAYER_ACCT_NUMBER,
                PAYER_OFFICE_CD=Constants.PAYER_OFFICE_CD,
                B10=Constants.BLANK_SPACE,
                AMT_CD_1=self._format_amount_fields(records.gross_payments),
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
                AMT_CD_H=Constants.AMT_CD_1,
                AMT_CD_J=Constants.AMT_CD_1,
                B16=Constants.BLANK_SPACE,
                FE_IND=Constants.BLANK_SPACE,
                PAYEE_NM1=self._get_full_name(records.first_name, records.last_name, "PAYEE_NM1"),
                PAYEE_NM2=self._get_full_name(records.first_name, records.last_name, "PAYEE_NM2"),
                PAYEE_ADDRESS=self._get_address_lines(
                    records.address_line_1, records.address_line_2
                ),
                B40_1=Constants.BLANK_SPACE,
                PAYEE_CTY=self._get_city(records.city),
                PAYEE_ST=self._get_state(records.state),
                PAYEE_ZC=self._get_zip(records.zip),
                B1=Constants.BLANK_SPACE,
                SEQ_NO=b_seq,
                B36=Constants.BLANK_SPACE,
                SEC_TIN_NOTICE=Constants.BLANK_SPACE,
                B2=Constants.BLANK_SPACE,
                TRADE_BUS_IND=Constants.BLANK_SPACE,
                TAX_YR_OF_REFUND=Constants.BLANK_SPACE,
                B111=Constants.BLANK_SPACE,
                SP_DATA_ENTRIES=Constants.BLANK_SPACE,
                ST_TAX=self._format_amount_fields(records.state_tax_withholdings),
                LOCAL_TAX=Constants.BLANK_SPACE,
                CSF_CD=Constants.COMBINED_ST_FED_CD,
            )
            b_record = template_str.format_map(b_dict)
            b_seq = b_seq + 1
            b_dict_list.append(b_record)
            self.seq_number = b_seq
        return b_dict_list

    def _load_c_rec_data(self, template_str: str, ctl_total: decimal.Decimal) -> str:
        c_seq = self.seq_number
        logger.info("c_seq %s", c_seq)
        c_dict = dict(
            C_REC_TYPE=Constants.C_REC_TYPE,
            TOT_B_REC=self.total_b_record,
            B6=Constants.BLANK_SPACE,
            CTL_TOTAL_1=ctl_total,
            CTL_TOTAL=Constants.ZERO,
            B160=Constants.BLANK_SPACE,
            SEQ_NO=c_seq,
            B241=Constants.BLANK_SPACE,
        )
        c_record = template_str.format_map(c_dict)
        self.seq_number += 1
        return c_record

    def _load_k_rec_data(
        self,
        template_str: str,
        ctl_total: decimal.Decimal,
        st_tax: decimal.Decimal,
        fed_tax: decimal.Decimal,
    ) -> str:
        k_seq = self.seq_number
        k_dict = dict(
            K_REC_TYPE=Constants.K_REC_TYPE,
            TOT_B_REC=self.total_b_record,
            B6=Constants.BLANK_SPACE,
            CTL_TOTAL_1=ctl_total,
            CTL_TOTAL=Constants.ZERO,
            B160=Constants.BLANK_SPACE,
            SEQ_NO=k_seq,
            B199=Constants.BLANK_SPACE,
            ST_TAX=st_tax,
            FED_TAX=fed_tax,
            B4=Constants.BLANK_SPACE,
            CSF_CD=Constants.COMBINED_ST_FED_CD,
        )
        k_record = template_str.format_map(k_dict)
        self.seq_number += 1
        return k_record

    def _load_f_rec_data(self, template_str: str) -> str:
        f_seq = self.seq_number
        f_dict = dict(
            F_REC_TYPE=Constants.F_REC_TYPE,
            TOT_A_REC=self.total_a_record,
            ZERO_21=Constants.ZERO,
            B19=Constants.BLANK_SPACE,
            TOT_B_REC=self.total_b_record,
            B442=Constants.BLANK_SPACE,
            SEQ_NO=f_seq,
            B241=Constants.BLANK_SPACE,
        )
        f_record = template_str.format_map(f_dict)
        return f_record

    def _get_full_name(self, fname: str, lname: str, field_name: str) -> str:

        first_name = self._replace_title(fname)
        last_name = self._replace_title(lname)
        full_name_str = last_name + " " + first_name
        full_name = self._remove_special_chars(full_name_str)
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

    def _get_name_ctl(self, last_name: str) -> str:
        last_name_four = ""
        lname = self._remove_special_chars_name_control(last_name)
        if lname.find("-") != -1:
            last_name = lname.split("-")[0]
        elif lname.find(" ") != -1:
            last_name_list = lname.split(" ")
            name_length = len(last_name_list)
            if name_length == 2:
                if not self._if_title_name_control(last_name_list[1]):
                    last_name = last_name_list[1]
                else:
                    last_name = last_name_list[0]
            else:
                last_name = last_name_list[0].rstrip() + last_name_list[1]
        else:
            last_name = lname
        last_name_four = last_name[0:4].upper()
        return last_name_four

    def _format_amount_fields(self, amt: decimal.Decimal) -> str:

        amount = str(amt).split(".")
        dollars = amount[0]
        if len(amount) == 2:
            cents = amount[1]
            if len(cents) == 2:
                cents = cents
            elif len(cents) == 1:
                cents = cents + "0"
            else:
                cents = cents[:2]
        else:
            cents = "00"
        format_amt = dollars + cents
        return format_amt

    def _get_totals(self, tax_data: List[Any]) -> Tuple:
        ctl_total = decimal.Decimal(0.0)
        st_tax = decimal.Decimal(0.0)
        fed_tax = decimal.Decimal(0.0)

        for records in tax_data:
            ctl_total += records.gross_payments
            st_tax += records.state_tax_withholdings
            fed_tax += records.federal_tax_withholdings
        return (
            self._format_amount_fields(ctl_total),
            self._format_amount_fields(st_tax),
            self._format_amount_fields(fed_tax),
        )

    def _get_correction_totals(self, tax_data: List[Any], correct_type: str) -> Tuple:
        ctl_total = decimal.Decimal(0.0)
        st_tax = decimal.Decimal(0.0)
        fed_tax = decimal.Decimal(0.0)

        for item in tax_data:
            # Add totals if it is one step correction or if it is
            # second step of a 2 step correction
            if (correct_type == "G" and item["correction_type"] != "C") or (
                correct_type == "C" and item["correction_type"] == "C"
            ):

                ctl_total += item["record"].gross_payments
                st_tax += item["record"].state_tax_withholdings
                fed_tax += item["record"].federal_tax_withholdings
        return (
            self._format_amount_fields(ctl_total),
            self._format_amount_fields(st_tax),
            self._format_amount_fields(fed_tax),
        )

    def _if_title_name_control(self, name_str: str) -> bool:

        titles = ["JR.", "JR", "II", "III", "SR", "SR.", "DR", "DR.", "MRS.", "MRS", "MR", "MR."]
        ret_value = False

        name_str = name_str.rstrip().upper()
        for title in titles:
            if title == name_str:
                ret_value = True
                break
        return ret_value

    def _replace_title(self, name_str: str) -> str:
        titles = ["DR.", "MR.", "MRS.", "DR ", "MR ", "MRS "]
        name_str = name_str.upper()
        for title in titles:
            if title in name_str:
                start_index = name_str.index(title)
                end_index = start_index + len(title)
                name_str = name_str.replace(name_str[start_index:end_index], "")
                name_str = name_str.rstrip()
                break
        return name_str

    def _get_city(self, city: str) -> str:

        city = city[:40].upper()
        return city

    def _get_state(self, st: str) -> str:
        state = st[:2].upper()
        return state

    def _get_zip(self, zip_code: str) -> str:
        zip_code_five = ""
        zip_code_four = ""
        zcode = ""
        if zip_code.find("-") != -1:
            zip_code_five = zip_code.split("-")[0]
            zip_code_four = zip_code.split("-")[1]
            zcode = zip_code_five[:5] + zip_code_four[:4]
        else:
            zcode = zip_code[:9]
        return zcode

    def _remove_special_chars(self, name_string: str) -> str:

        final_string = re.sub("[^A-Za-z0-9- &]+", "", name_string)
        if final_string != name_string:
            logger.info("Removed special characters from name.")
        return final_string

    def process_correction_types(self, corrected_tax_data: List[Any]) -> Tuple:

        g_correction_list = []
        c_correction_list = []
        for record in corrected_tax_data:

            last_submitted_pfml_id = record.pfml_1099_id
            latest_pfml_id = record.latest_pfml_1099_id
            batch_id = record.latest_pfml_batch_id
            pfml_1099s = pfml_1099_util.get_old_new_1099_record(
                self.db_session, last_submitted_pfml_id, latest_pfml_id, record.employee_id
            )
            """The first record is previously submitted record and second record is the new one"""
            if pfml_1099s[0] is not None and pfml_1099s[1] is not None:

                """
                For G correction:
                b- Only scenario in our case.
                a is always amt code 1(add amt code 4 for fedtax) for 1099
                c,d Not applicable
                a. Incorrect payment amount codes in the
                Issuer “A” Record.
                b. Incorrect payment amounts in the Payee
                c. Incorrect code in the distribution code field in the
                Payee “B” Record.
                d. Incorrect payee indicator. (Payee indicators are
                non-money amount indicator fields found in the
                specific form record layouts of the Payee “B”
                Record between field positions544-748). -G correction
                C- Correction - a,b,c in our case, d is hardcoded as 'F'
                a. No payee TIN (SSN, EIN, ITIN, QI-EIN, ATIN)
                b. Incorrect payee TIN
                c. Incorrect payee name
                d. Wrong type of return indicator"""

                if pfml_1099s[0].gross_payments != pfml_1099s[1].gross_payments:
                    g_correction_list.append(dict(record=pfml_1099s[1], correction_type="G"))
                    self.increment(self.Metrics.IRS_FILE_1099_G_CORRECTION_COUNT)

                if (
                    pfml_1099s[0].tax_identifier_id != pfml_1099s[1].tax_identifier_id
                    or pfml_1099s[0].first_name != pfml_1099s[1].first_name
                    or pfml_1099s[0].last_name != pfml_1099s[1].last_name
                ):

                    c_correction_list.append(dict(record=pfml_1099s[1], correction_type="C"))
                    g_correction_list.append(dict(record=pfml_1099s[1], correction_type="C"))
                    self.increment(self.Metrics.IRS_FILE_1099_C_CORRECTION_COUNT)

        return g_correction_list, c_correction_list, batch_id

    def _remove_special_chars_name_control(self, name_string: str) -> str:

        final_string = re.sub("[^A-Za-z0-9- ]+", "", name_string)
        if final_string != name_string:
            logger.info("Removed special characters from name control.")
        return final_string

    def _get_address_lines(self, line1: str, line2: str) -> str:

        address_line_str = line1 + " " + line2
        address_lines = self._remove_special_chars(address_line_str)
        address_line_forty = address_lines[:40].upper()

        return address_line_forty
