-- PFML Payment Summary Report
WITH PAYMENT_BATCH_TRANSACTIONS AS (
    SELECT P.PAYMENT_ID, P.PERIOD_START_DATE, P.PERIOD_END_DATE, P.PAYMENT_DATE,  P.AMOUNT, 
           C.FINEOS_ABSENCE_ID, C.ABSENCE_PERIOD_START_DATE, C.ABSENCE_PERIOD_END_DATE,
           CT.CLAIM_TYPE_ID, CT.CLAIM_TYPE_DESCRIPTION, E.FINEOS_CUSTOMER_NUMBER, FAS.ABSENCE_STATUS_DESCRIPTION,
           P.FINEOS_PEI_C_VALUE,  P.FINEOS_PEI_I_VALUE,  P.FINEOS_EXTRACTION_DATE,
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
    LEFT OUTER JOIN EMPLOYEE E ON C.EMPLOYEE_ID = E.EMPLOYEE_ID
    INNER JOIN STATE_LOG SL ON P.PAYMENT_ID = SL.PAYMENT_ID
    INNER JOIN LK_STATE ST1 ON SL.END_STATE_ID = ST1.STATE_ID
    WHERE ST1.FLOW_ID IN (21)
      AND P.FINEOS_EXTRACT_IMPORT_LOG_ID = (SELECT MAX(IMPORT_LOG_ID)
                                            FROM IMPORT_LOG
                                            WHERE SOURCE = 'PaymentExtractStep'))
SELECT 'Total Payments' "Name", to_char(COUNT(*), '990') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'Checks Payments' "Name", to_char(SUM(PBT.AMOUNT), '999,999,990D99') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'Checks Payments' "Name", to_char(SUM(CASE WHEN PBT.CURRENT_STATE_ID IN (137) THEN 1 ELSE 0 END), '999,999,990') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'Checks Payment Amount' "Name", to_char(SUM(CASE WHEN PBT.CURRENT_STATE_ID IN (137) THEN PBT.AMOUNT ELSE 0 END), '999,999,990D99') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'ACH Payments' "Name", to_char(SUM(CASE WHEN PBT.CURRENT_STATE_ID IN (139) THEN 1 ELSE 0 END), '999,999,990') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'ACH Payment Amount' "Name", to_char(SUM(CASE WHEN PBT.CURRENT_STATE_ID IN (139) THEN PBT.AMOUNT ELSE 0 END), '999,999,990D00') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'Family Leave Payments' "Name", to_char(SUM(CASE WHEN PBT.CLAIM_TYPE_ID = 1 THEN 1 ELSE 0 END), '999,999,990') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'Family Leave Payment Amount' "Name", to_char(SUM(CASE WHEN PBT.CLAIM_TYPE_ID = 1 THEN PBT.AMOUNT ELSE 0 END), '999,999,990D00') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'Medical Leave Payments' "Name", to_char(SUM(CASE WHEN PBT.CLAIM_TYPE_ID = 2 THEN 1 ELSE 0 END), '999,999,990') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'Medical Leave Payment Amount' "Name", to_char(SUM(CASE WHEN PBT.CLAIM_TYPE_ID = 2 THEN PBT.AMOUNT ELSE 0 END), '999,999,990D00') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'Military Leave Payments' "Name", to_char(SUM(CASE WHEN PBT.CLAIM_TYPE_ID = 3 THEN 1 ELSE 0 END), '999,999,990') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
UNION ALL
SELECT 'Military Leave Payment Amount' "Name", to_char(SUM(CASE WHEN PBT.CLAIM_TYPE_ID = 3 THEN PBT.AMOUNT ELSE 0 END), '999,999,990D00') "Value"
FROM PAYMENT_BATCH_TRANSACTIONS PBT WHERE PBT.IS_CURRENT = 'Y'  AND PBT.CURRENT_STATE_ID IN (137, 139)
