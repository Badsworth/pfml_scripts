-- PFML Address Error Report
WITH PAYMENT_BATCH_TRANSACTIONS AS (
    SELECT P.PAYMENT_ID, P.PERIOD_START_DATE, P.PERIOD_END_DATE, P.PAYMENT_DATE,  P.AMOUNT, 
           C.FINEOS_ABSENCE_ID, C.ABSENCE_PERIOD_START_DATE, C.ABSENCE_PERIOD_END_DATE,
           CT.CLAIM_TYPE_DESCRIPTION, E.FINEOS_CUSTOMER_NUMBER, FAS.ABSENCE_STATUS_DESCRIPTION,
           P.FINEOS_PEI_C_VALUE,  P.FINEOS_PEI_I_VALUE,  P.FINEOS_EXTRACTION_DATE,
           CASE WHEN P.DISB_METHOD_ID = 1 THEN 'ACH'
                WHEN P.DISB_METHOD_ID = 2 THEN 'Check'
           END PAYMENT_DIST_METHOD,
           LAG(ST1.STATE_DESCRIPTION) OVER(PARTITION BY P.PAYMENT_ID ORDER BY SL.STARTED_AT) AS PRIOR_STATE,
           SL.OUTCOME,
           ST1.STATE_ID AS CURRENT_STATE_ID,
           ST1.STATE_DESCRIPTION AS CURRENT_STATE,
           LEAD(ST1.STATE_DESCRIPTION) OVER(PARTITION BY P.PAYMENT_ID ORDER BY SL.STARTED_AT) AS NEXT_STATE,
           SL.STARTED_AT AS EFFECTIVE_START,
           COALESCE(LEAD(SL.STARTED_AT) OVER(PARTITION BY P.PAYMENT_ID ORDER BY SL.STARTED_AT), DATE '9999-12-31') AS EFFECTIVE_END,
           CASE WHEN LEAD(SL.STARTED_AT) OVER(PARTITION BY P.PAYMENT_ID ORDER BY SL.STARTED_AT) IS NULL THEN 'Y' ELSE 'N' END AS IS_CURRENT
    FROM PAYMENT P
    LEFT OUTER JOIN CLAIM C ON P.CLAIM_ID = C.CLAIM_ID
    LEFT OUTER JOIN LK_CLAIM_TYPE CT ON CT.CLAIM_TYPE_ID = C.CLAIM_TYPE_ID
    LEFT OUTER JOIN LK_ABSENCE_STATUS FAS ON C.FINEOS_ABSENCE_STATUS_ID = FAS.ABSENCE_STATUS_ID
    LEFT OUTER JOIN EMPLOYEE E ON P.EMPLOYEE_ID = E.EMPLOYEE_ID
    INNER JOIN STATE_LOG SL ON P.PAYMENT_ID = SL.PAYMENT_ID
    INNER JOIN LK_STATE ST1 ON SL.END_STATE_ID = ST1.STATE_ID
    WHERE ST1.FLOW_ID IN (21)
      AND P.FINEOS_EXTRACT_IMPORT_LOG_ID = (SELECT MAX(IMPORT_LOG_ID)
                                            FROM IMPORT_LOG
                                            WHERE SOURCE = 'PaymentExtractStep'))
SELECT PBT.FINEOS_CUSTOMER_NUMBER "Customer Number",
       PBT.FINEOS_ABSENCE_ID "NTN Number", 
       PBT.CLAIM_TYPE_DESCRIPTION "Absence Case Type",
       PBT.ABSENCE_STATUS_DESCRIPTION "Absence Status",
	   PBT.PAYMENT_DIST_METHOD "Payment Method",
       PBT.ABSENCE_PERIOD_START_DATE "Absence Period Start Date", 
       PBT.ABSENCE_PERIOD_END_DATE "Absence Period End Date",
       PBT.PERIOD_START_DATE "Payment Period Start Date", 
       PBT.PERIOD_END_DATE "Payment Period End Date", 
       PBT.PAYMENT_DATE "Payment Date", 
       PBT.AMOUNT "Payment Amount", 
       PBT.FINEOS_PEI_C_VALUE "C", 
       PBT.FINEOS_PEI_I_VALUE "I", 
       PBT.FINEOS_EXTRACTION_DATE "Fineos Extraction Date",
       PBT.OUTCOME::json#>'{experian_result,input_address}' "Address Provided",
       PBT.OUTCOME::json#>'{experian_result,confidence}' result,
       PBT.OUTCOME::json#>'{experian_result,output_address_1}' "Experian Address Recommendation #1",
       PBT.OUTCOME::json#>'{experian_result,output_address_2}' "Experian Address Recommendation #2",
       PBT.OUTCOME::json#>'{experian_result,output_address_3}' "Experian Address Recommendation #3",
       PBT.OUTCOME::json#>'{experian_result,output_address_4}' "Experian Address Recommendation #4",
       PBT.OUTCOME::json#>'{experian_result,output_address_5}' "Experian Address Recommendation #5",
       PBT.OUTCOME::json#>'{experian_result,output_address_6}' "Experian Address Recommendation #6",
       PBT.OUTCOME::json#>'{experian_result,output_address_7}' "Experian Address Recommendation #7",
       PBT.OUTCOME::json#>'{experian_result,output_address_8}' "Experian Address Recommendation #8"
FROM PAYMENT_BATCH_TRANSACTIONS PBT
WHERE PBT.IS_CURRENT = 'Y'
  AND PBT.CURRENT_STATE_ID IN (156)
