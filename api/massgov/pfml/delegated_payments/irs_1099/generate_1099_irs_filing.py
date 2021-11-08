import os

import massgov.pfml.delegated_payments.delegated_config as paymentConfig
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)

total_b_record = 0


class Constants:
    T_REC_TYPE = "T"
    A_REC_TYPE = "A"
    B_REC_TTYPE = "B"
    C_RECT_TYPE = "C"
    K_RECT_TYPE = "K"
    F_RECT_TYPE = "F"
    PY_IND = " "
    TX_CTL_NO = "08025"
    TX_NAME = "COMMONWEALTH OF MASSACHUSETTS"
    TAX_YEAR = 2021
    COM_NM = "COMMONWEALTH OF MASSACHUSETTS"
    COM_ADDR = "One Ashburton PL,Room 901"
    COM_CTY = "BOSTON"
    COM_ST = "MA"
    COM_ZIP_CD = "02108"
    CONT_NM = "Jessica A Cogswell"
    CONT_PH = "6179732323"
    CONT_EMAIL = "jessica.cogswell@mass.gov"
    VEN_IND = "I"
    TOT_B_REC = 10
    PAYER_TIN = "046000284"
    PAYER_LNAME = "COMM"
    PAYER_OFFICE_CD = ""
    PAYER_ACC_NO = ""
    RETURN_TYPE = "F"
    AMT_CD = 1
    TA_IND = 0
    PYR_PHONE = 6179732323
    A_REC_COUNT = 1
    COMBINED_ST_FED_IND = ""
    PREVIOUS_YR_IND = ""
    SECOND_TIN_NOTICE = ""
    TIN_TYPE = 2
    TAX_YR_OF_REFUND = ""
    BLANK_SPACE = " "
    FILE_NAME = "1099.org"
    G1099_FILENAME_FORMAT = f"%Y-%m-%d-%H-%M-%S-{FILE_NAME}"


class Generate1099IRSfilingStep(Step):
    def run_step(self) -> None:
        self._generate_1099_irs_filing()

    def _generate_1099_irs_filing(self) -> None:
        logger.debug("1099 Documents - Generate 1099.org file to be transmitted to IRS")

        t_template = self._create_t_template()
        t_entries = self._load_t_rec_data(t_template)
        a_template = self._create_a_template()
        a_entries = self._load_a_rec_data(a_template)
        entries = t_entries + a_entries
        self._create_irs_file(entries)

    def _create_t_template(self) -> str:
        temp = (
            "{T_REC_TYPE:<1}{TAX_YEAR:<4}{PY_IND:<1}{TX_TIN:<9}{TX_CTL_NO:<5}{B7:<7}"
            "{TST_FILE_IND:<1}{FOR_IND:<1}{TX_NAME:<80}{COMP_NAME:<80}{COMP_ADDR:<40}"
            "{COMP_CTY:<40}{COMP_ST:<2}{COMP_ZIP_CD:0<9}{B15:<15}{TOT_B_REC:08}"
            "{CONT_NM:<40}{CONT_PH:<15}{CONT_EMAIL:<50}{B91:<91}{REC_SEQ_NO:08}{B10:<10}"
            "{VEN_IND:<1}{VEN_INFO:<232}\n"
        )
        logger.debug("Template string is %s", temp)
        return temp

    def _create_a_template(self) -> str:
        temp = (
            "{A_REC_TYPE:<1}{TAX_YEAR:<4}{PY_IND:<1}{CSF_IND:<1}{B5:<5}{PYR_TIN:<9}"
            "{PYR_NM_CTL:<4}{LAST_FILING_IND:<1}{TYPE_RET:<2}{AMT_CD:016}{B8:<8}"
            "{FE_IND:<1}{PYR_NM:<80}{TA_IND:<1}{PYR_ADDR:<40}{PYR_CTY:<40}"
            "{PYR_ST:<2}{PYR_ZC:0<9}{PYR_PHONE:<15}{B260:<260}{SEQ_NO:08}{B243:<243}\n"
        )
        logger.debug("Template string is %s", temp)
        return temp

    def _create_irs_file(self, all_records: str) -> None:

        logger.debug("creating irs file")
        s3_config = paymentConfig.get_s3_config()
        now = payments_util.get_now()
        source_path = s3_config.pfml_error_reports_archive_path
        dfml_sharepoint_outgoing_path = s3_config.dfml_report_outbound_path
        source_path = payments_util.build_archive_path(
            source_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            now.strftime(Constants.G1099_FILENAME_FORMAT),
            now,
        )
        with file_util.write_file(source_path) as irs_file:
            irs_file.write(all_records)
        outgoing_s3_path = os.path.join(dfml_sharepoint_outgoing_path, Constants.FILE_NAME)
        file_util.copy_file(source_path, outgoing_s3_path)

    def _load_t_rec_data(self, template_str: str) -> str:
        t_dict = dict(
            T_REC_TYPE=Constants.T_REC_TYPE,
            PY_IND=Constants.PY_IND,
            TAX_YEAR=Constants.TAX_YEAR,
            TX_TIN=Constants.PAYER_TIN,
            TX_CTL_NO=Constants.TX_CTL_NO,
            B7=Constants.BLANK_SPACE,
            TST_FILE_IND=Constants.BLANK_SPACE,
            FOR_IND=Constants.BLANK_SPACE,
            TX_NAME=Constants.TX_NAME,
            COMP_NAME=Constants.COM_NM,
            COMP_ADDR=Constants.COM_ADDR,
            COMP_CTY=Constants.COM_CTY,
            COMP_ST=Constants.COM_ST,
            COMP_ZIP_CD=Constants.COM_ZIP_CD,
            B15=Constants.BLANK_SPACE,
            TOT_B_REC=total_b_record,
            CONT_NM=Constants.CONT_NM,
            CONT_PH=Constants.CONT_PH,
            CONT_EMAIL=Constants.CONT_EMAIL,
            B91=Constants.BLANK_SPACE,
            REC_SEQ_NO=1,
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
            PY_IND=Constants.PY_IND,
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
