-- PFML Payment Error Report
SELECT P.PAYMENT_ID "Payment ID", 
       C.FINEOS_ABSENCE_ID "NTN Number", 
       C.ABSENCE_PERIOD_START_DATE "Absence Period Start Date", 
       C.ABSENCE_PERIOD_END_DATE "Absence Period End Date",
       P.PERIOD_START_DATE "Payment Period Start Date", 
       P.PERIOD_END_DATE "Payment Period End Date", 
       P.PAYMENT_DATE "Payment Date", 
       P.AMOUNT "Payment Amount", 
       P.FINEOS_PEI_C_VALUE "C", 
       P.FINEOS_PEI_I_VALUE "I", 
       P.FINEOS_EXTRACTION_DATE "Fineos Extraction Date", 
       SL.OUTCOME->>'message' "Error Message",
       json_array_elements(SL.OUTCOME->'validation_container'->'validation_issues')->>'reason' "Reason",
       json_array_elements(SL.OUTCOME->'validation_container'->'validation_issues')->>'details' "Details"
FROM PAYMENT P
LEFT OUTER JOIN CLAIM C ON P.CLAIM_ID = C.CLAIM_ID
INNER JOIN STATE_LOG SL ON P.PAYMENT_ID = SL.PAYMENT_ID
INNER JOIN LK_STATE ST1 ON SL.END_STATE_ID = ST1.STATE_ID
WHERE P.FINEOS_EXTRACT_IMPORT_LOG_ID = (SELECT MAX(IMPORT_LOG_ID)
                                        FROM IMPORT_LOG
                                        WHERE SOURCE = 'PaymentExtractStep')
  AND ST1.STATE_ID = 120 
