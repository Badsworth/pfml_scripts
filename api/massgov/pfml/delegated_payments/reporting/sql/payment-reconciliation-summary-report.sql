-- PFML Payment Processing Reconciliation Report
WITH PAYMENT_BATCH_TRANSACTIONS AS (
    SELECT P.PAYMENT_ID, SL.OUTCOME,
           LAG(ST1.STATE_DESCRIPTION) OVER(PARTITION BY P.PAYMENT_ID ORDER BY SL.STARTED_AT) AS PRIOR_STATE,
           ST1.STATE_DESCRIPTION AS CURRENT_STATE,
           LEAD(ST1.STATE_DESCRIPTION) OVER(PARTITION BY P.PAYMENT_ID ORDER BY SL.STARTED_AT) AS NEXT_STATE,
           SL.STARTED_AT AS EFFECTIVE_START,
           COALESCE(LEAD(SL.STARTED_AT) OVER(PARTITION BY P.PAYMENT_ID ORDER BY SL.STARTED_AT), DATE '9999-12-31') AS EFFECTIVE_END,
           CASE WHEN LEAD(SL.STARTED_AT) OVER(PARTITION BY P.PAYMENT_ID ORDER BY SL.STARTED_AT) IS NULL THEN 'Y' ELSE 'N' END AS IS_CURRENT
    FROM PAYMENT P
    INNER JOIN STATE_LOG SL ON P.PAYMENT_ID = SL.PAYMENT_ID
    INNER JOIN LK_STATE ST1 ON SL.END_STATE_ID = ST1.STATE_ID
    WHERE P.FINEOS_EXTRACT_IMPORT_LOG_ID = (SELECT MAX(IMPORT_LOG_ID)
                                            FROM IMPORT_LOG
                                            WHERE SOURCE = 'PaymentExtractStep'))
SELECT CASE
         WHEN CURRENT_STATE = 'Add employer reimbursement payment to FINEOS Writeback' THEN 'Employer Reimbursment'
         WHEN CURRENT_STATE = 'Add to PUB Transaction - Check' THEN 'PUB Check'
         WHEN CURRENT_STATE = 'Add to PUB Transaction - ACH' THEN 'PUB ACH'
         WHEN CURRENT_STATE = 'Add to Payment Error Report' THEN 'Payment Error'
         WHEN CURRENT_STATE = '$0 payment FINEOS Writeback sent' THEN 'Zero Dollar Payment'
         ELSE CURRENT_STATE
	   END "Payment Status", 
       COUNT(*) "Payment Records"
FROM PAYMENT_BATCH_TRANSACTIONS PBT
WHERE IS_CURRENT = 'Y'
GROUP BY CURRENT_STATE
ORDER BY COUNT(*) DESC

