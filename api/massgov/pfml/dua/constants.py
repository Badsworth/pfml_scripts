class Metrics:
    # demographics
    DUA_DEMOGRAPHICS_FILE_DOWNLOADED_COUNT = "dua_demographics_file_downloaded_count"
    PENDING_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT = (
        "pending_dua_demographics_reference_files_count"
    )
    SUCCESSFUL_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT = (
        "successful_dua_demographics_reference_files_count"
    )
    TOTAL_DUA_DEMOGRAPHICS_ROW_COUNT = "total_dua_demographics_row_count"
    UNSUCCESSFUL_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT = (
        "unsuccessful_dua_demographics_reference_files_count"
    )
    INSERTED_DUA_DEMOGRAPHICS_ROW_COUNT = "inserted_dua_demographics_row_count"
    EMPLOYEE_SKIPPED_COUNT = "employee_skipped_count"
    OCCUPATION_ORG_UNIT_SET_COUNT = "occupation_org_unit_set_count"
    OCCUPATION_ORG_UNIT_SKIPPED_COUNT = "occupation_org_unit_skipped_count"
    MISSING_DUA_REPORTING_UNIT_COUNT = "missing_dua_reporting_unit_count"
    CREATED_EMPLOYEE_OCCUPATION_COUNT = "created_employee_occupation_count"
    DUA_REPORTING_UNIT_MISSING_FINEOS_ORG_UNIT_COUNT = (
        "dua_reporting_unit_missing_fineos_org_unit_count"
    )
    DUA_REPORTING_UNIT_MISMATCHED_EMPLOYER_COUNT = "dua_reporting_unit_mismatched_employer_count"

    # employer
    DUA_EMPLOYER_FILE_DOWNLOADED_COUNT = "dua_employer_file_downloaded_count"
    PENDING_DUA_EMPLOYER_REFERENCE_FILES_COUNT = "pending_dua_employer_reference_files_count"
    SUCCESSFUL_DUA_EMPLOYER_REFERENCE_FILES_COUNT = "successful_dua_employer_reference_files_count"
    TOTAL_DUA_EMPLOYER_ROW_COUNT = "total_dua_employer_row_count"
    UNSUCCESSFUL_DUA_EMPLOYER_REFERENCE_FILES_COUNT = (
        "unsuccessful_dua_employer_reference_files_count"
    )
    INSERTED_DUA_EMPLOYER_ROW_COUNT = "inserted_dua_employer_row_count"

    # employer unit
    DUA_EMPLOYER_UNIT_FILE_DOWNLOADED_COUNT = "dua_employer_unit_file_downloaded_count"
    PENDING_DUA_EMPLOYER_UNIT_REFERENCE_FILES_COUNT = (
        "pending_dua_employer_unit_reference_files_count"
    )
    SUCCESSFUL_DUA_EMPLOYER_UNIT_REFERENCE_FILES_COUNT = (
        "successful_dua_employer_unit_reference_files_count"
    )
    TOTAL_DUA_EMPLOYER_UNIT_ROW_COUNT = "total_employer_unit_row_count"
    UNSUCCESSFUL_DUA_EMPLOYER_UNIT_REFERENCE_FILES_COUNT = (
        "unsuccessful_dua_employer_unit_reference_files_count"
    )
    INSERTED_DUA_EMPLOYER_UNIT_ROW_COUNT = "inserted_dua_employer_unit_row_count"


class Constants:
    CUSTOMER_ID_FIELD = "FINEOS"
    EMPR_FEIN_FIELD = "FEIN"
    DOB_FIELD = "BirthDt"
    GENDER_CODE_FIELD = "GenderCd"
    OCCUPATION_CODE_FIELD = "OccupationCode"
    OCCUPATION_DESCRIPTION_FIELD = "OccupationDesc"
    EMPR_REPORTING_UNIT_NO_FIELD = "EmployerUnitNumber"
    FINEOS_EMPLOYER_ID_FIELD = "FineosEmployerID"
    DBA_FIELD = "DBA"
    DUA_ID_FIELD = "DUA"
    ATTENTION_FIELD = "Attention"
    EMAIL_FIELD = "Email"
    PHONE_NUMBER_FIELD = "PhoneNumber"
    ADDRESS_LINE_ONE_FILED = "AddressLine1"
    ADDRESS_LINE_TWO_FILED = "AddressLine2"
    ADDRESS_CITY_FIELD = "AddressCity"
    ADDRESS_ZIP_CODE_FIELD = "ZipCode"
    ADDRESS_STATE_FIELD = "State"
    NAICS_CODE_FIELD = "NAICS"
    NAICS_DESCRIPTION_FIELD = "NAICSDesc"

    DUA_DEMOGRAPHIC_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP = {
        CUSTOMER_ID_FIELD: "fineos_customer_number",
        DOB_FIELD: "date_of_birth",
        GENDER_CODE_FIELD: "gender_code",
        OCCUPATION_CODE_FIELD: "occupation_code",
        OCCUPATION_DESCRIPTION_FIELD: "occupation_description",
        EMPR_FEIN_FIELD: "employer_fein",
        EMPR_REPORTING_UNIT_NO_FIELD: "employer_reporting_unit_number",
    }

    DUA_EMPLOYER_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP = {
        FINEOS_EMPLOYER_ID_FIELD: "fineos_employer_id",
        DBA_FIELD: "dba",
        ATTENTION_FIELD: "attention",
        EMAIL_FIELD: "email",
        PHONE_NUMBER_FIELD: "phone_number",
        ADDRESS_LINE_ONE_FILED: "address_line_1",
        ADDRESS_LINE_TWO_FILED: "address_line_2",
        ADDRESS_CITY_FIELD: "address_city",
        ADDRESS_ZIP_CODE_FIELD: "address_zip_code",
        ADDRESS_STATE_FIELD: "address_state",
        NAICS_CODE_FIELD: "naics_code",
        NAICS_DESCRIPTION_FIELD: "naics_description",
    }

    DUA_EMPLOYER_UNIT_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP = {
        FINEOS_EMPLOYER_ID_FIELD: "fineos_employer_id",
        DUA_ID_FIELD: "dua_id",
        DBA_FIELD: "dba",
        ATTENTION_FIELD: "attention",
        EMAIL_FIELD: "email",
        PHONE_NUMBER_FIELD: "phone_number",
        ADDRESS_LINE_ONE_FILED: "address_line_1",
        ADDRESS_LINE_TWO_FILED: "address_line_2",
        ADDRESS_CITY_FIELD: "address_city",
        ADDRESS_ZIP_CODE_FIELD: "address_zip_code",
        ADDRESS_STATE_FIELD: "address_state",
    }
