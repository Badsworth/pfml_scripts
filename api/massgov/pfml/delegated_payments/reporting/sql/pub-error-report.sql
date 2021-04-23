-- PFML PUB Error Report
WITH PAYMENT_BATCH_TRANSACTIONS AS (
    SELECT P.PAYMENT_ID, P.PERIOD_START_DATE, P.PERIOD_END_DATE, P.PAYMENT_DATE,  P.AMOUNT, 
           C.FINEOS_ABSENCE_ID, C.ABSENCE_PERIOD_START_DATE, C.ABSENCE_PERIOD_END_DATE,
           CT.CLAIM_TYPE_DESCRIPTION, E.FINEOS_CUSTOMER_NUMBER, FAS.ABSENCE_STATUS_DESCRIPTION,
           P.FINEOS_PEI_C_VALUE,  P.FINEOS_PEI_I_VALUE,  P.FINEOS_EXTRACTION_DATE,
           PE.MESSAGE, PE.DETAILS -- PUB_ERROR_TYPE_ID, LINE_NUMBER, TYPE_CODE, REFERENCE_FILE_ID
    FROM PUB_ERROR PE
	LEFT OUTER JOIN PAYMENT P ON PE.PAYMENT_ID = P.PAYMENT_ID
    LEFT OUTER JOIN CLAIM C ON P.CLAIM_ID = C.CLAIM_ID
	LEFT OUTER JOIN LK_CLAIM_TYPE CT ON CT.CLAIM_TYPE_ID = C.CLAIM_TYPE_ID
	LEFT OUTER JOIN LK_ABSENCE_STATUS FAS ON C.FINEOS_ABSENCE_STATUS_ID = FAS.ABSENCE_STATUS_ID
	LEFT OUTER JOIN EMPLOYEE E ON C.EMPLOYEE_ID = E.EMPLOYEE_ID
    WHERE PE.IMPORT_LOG_ID IN (SELECT MAX(IMPORT_LOG_ID)
                               FROM IMPORT_LOG
                               WHERE SOURCE = 'ProcessNachaReturnFileStep'
							   UNION ALL
                               SELECT MAX(IMPORT_LOG_ID)
                               FROM IMPORT_LOG
                               WHERE SOURCE = 'ProcessCheckReturnFileStep'
                               UNION ALL
                               SELECT MAX(IMPORT_LOG_ID)
                               FROM IMPORT_LOG
                               WHERE SOURCE = 'ProcessCheckReturnFileStep'
                                 AND IMPORT_LOG_ID < (SELECT MAX(IMPORT_LOG_ID)
                                                      FROM IMPORT_LOG
                                                      WHERE SOURCE = 'ProcessCheckReturnFileStep')))
SELECT PBT.FINEOS_CUSTOMER_NUMBER "Customer Number",
       PBT.FINEOS_ABSENCE_ID "NTN Number", 
       PBT.CLAIM_TYPE_DESCRIPTION "Absence Case Type",
       PBT.ABSENCE_STATUS_DESCRIPTION "Absence Status",
       PBT.ABSENCE_PERIOD_START_DATE "Absence Period Start Date", 
       PBT.ABSENCE_PERIOD_END_DATE "Absence Period End Date",
       PBT.PERIOD_START_DATE "Payment Period Start Date", 
       PBT.PERIOD_END_DATE "Payment Period End Date", 
       PBT.PAYMENT_DATE "Payment Date", 
       PBT.AMOUNT "Payment Amount", 
       PBT.FINEOS_PEI_C_VALUE "C", 
       PBT.FINEOS_PEI_I_VALUE "I", 
       PBT.FINEOS_EXTRACTION_DATE "Fineos Extraction Date", 
	   PBT.MESSAGE,
	   PBT.DETAILS,
--       PBT.OUTCOME->>'message' "Error Message",
--       json_array_elements(PBT.OUTCOME->'validation_container'->'validation_issues')->>'reason' "Reason",
--       json_array_elements(PBT.OUTCOME->'validation_container'->'validation_issues')->>'details' "Details", 
       PBT.PAYMENT_ID "Payment ID"
FROM PAYMENT_BATCH_TRANSACTIONS PBT