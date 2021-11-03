import enum
from random import paretovariate
from typing import List
from sqlalchemy.sql.functions import count

from sqlalchemy.sql.sqltypes import Boolean
from massgov.pfml.util.batch import log
import massgov.pfml.api.app as app

from sqlalchemy.orm import session
from sqlalchemy.sql.expression import distinct, false, label, true
from sqlalchemy import func
from massgov.pfml.delegated_payments.delegated_fineos_payment_extract import PaymentData
from massgov.pfml.db.models.payments import LinkSplitPayment
from massgov.pfml.delegated_payments.step import Step
import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.employees import Claim, Payment, State, StateLog,LatestStateLog,LkState,Flow
# import massgov.pfml.db as db
# import massgov.pfml.db
from massgov.pfml import db
import massgov.pfml.util.logging as logging
logger = logging.get_logger(__package__)

class RelatedPaymentsProcessingStep(Step):
	class Metrics(str, enum.Enum):
	 FEDERAL_WITHHOLDING_RECORD_COUNT = "federal_withholding_record_count"
	 STATE_WITHHOLDING_RECORD_COUNT = "state_withholding_record_count"

	def run_step(self) -> None:
		# with app.db_session() as db_session:
		logger.info("### :Start - process_payments_for_split_payments")
		self.process_payments_for_split_payments()
		logger.info("### :End - process_payments_for_split_payments")
		

	def process_payments_for_split_payments(self) -> None:
		"""
		Top-level function that calls all the other functions in this file in order
		"""
		logger.info("Processing related payment processing step")

		#get withholding payment records
		logger.info("### :begin - _get_withholding_payments_records")
		payments : List[Payment] = self._get_withholding_payments_records()
		logger.info(payments)
		logger.info("### :end - _get_withholding_payments_records")
		if not payments:
			logger.info("No payment records for related payment. Exiting early.")
			return

		for payment in payments:
			#get absense id for this payment
				fineos_absence_id = (
				self.db_session.query(distinct(Claim.fineos_absence_id))
				# .join(Claim, Payment.claim_id == Claim.claim_id)
				.filter(Claim.claim_id == payment.claim_id)
				.filter(Payment.payment_id == payment.payment_id)
				.first()
				)
				logger.info(fineos_absence_id[0])
			
				#get records for the absense id and check for duplicates
				is_duplicate_records_exists =   self.is_withholding_records_have_duplicate_records(
				self.db_session,payment,fineos_absence_id[0]
				)

				if(is_duplicate_records_exists):
						logger.info("Duplicate records exists for %s",fineos_absence_id[0])
					# to update status we need payment so getting all the payment details from above query
						#get duplicate payment records 
						duplicate_payment_records = (
							self.db_session.query(Payment)
							.filter(Payment.claim_id == payment.claim_id)
							.filter(Claim.fineos_absence_id == fineos_absence_id[0])
							.filter(Payment.period_start_date == payment.period_start_date)
							.filter(Payment.period_end_date == payment.period_end_date)
							.filter(Payment.payment_date == payment.payment_date)
							.filter(Payment.amount == payment.amount)
							.filter(Payment.fineos_extraction_date == payment.fineos_extraction_date)
							.all()
						)

						logger.info("duplicate payment records %s",duplicate_payment_records)

						payment_end_state_id = (
						self.db_session.query(StateLog.end_state_id)
						.join(Payment)
						.join(LkState, StateLog.end_state_id == LkState.state_id)
						.filter(
							Payment.payment_id ==payment.payment_id,
							StateLog.end_state_id.in_([191,195]),
						)
						.first()
						)

						logger.info(payment_end_state_id)


						logger.info("payment_end_state_id %s",payment_end_state_id[0])
						
						end_state =State.STATE_WITHHOLDING_PENDING_AUDIT if(payment_end_state_id[0] in [191]) else  State.FEDERAL_WITHHOLDING_PENDING_AUDIT
						logger.info("end_state_id %s",end_state)
						message = "Duplicate records found for the payment."

						for pmnt in duplicate_payment_records:
							state_log_util.create_finished_state_log(
							end_state=end_state,
							outcome=state_log_util.build_outcome(message),
							associated_model=pmnt,
							db_session=self.db_session,
							)
							logger.info(
							"Payment added to state %s",
							end_state.state_description,
							)
				else:


					# with app.db_session() as db_session:
					primary_payment_record = self._get_primary_payment_record(self.db_session,payment)
					logger.info(primary_payment_record)
					if(primary_payment_record ==""): 
						raise Exception(f"Primary payment id not found for withholding payment id: {payment.payment_id}")


					payment_id=primary_payment_record
					related_payment_id =payment.payment_id
					logger.info(payment_id)
					logger.info(related_payment_id)
					linkPayment = LinkSplitPayment()
					linkPayment.payment_id=payment_id
					linkPayment.related_payment_id=related_payment_id
					self.db_session.add(linkPayment)
		self.db_session.commit()

	
	def _get_withholding_payments_records(self) -> List[Payment]:
		"""this method appends fedral and state withholding payment records"""
		logger.info("### :begin - _get_payments_for_federal_withholding")
		federal_withholding_payments = self._get_payments_for_federal_withholding(self.db_session)
		logger.info("### :end - _get_payments_for_federal_withholding")
		state_withholding_payments = self._get_payments_for_state_withholding(self.db_session)
		Payment_containers = []
		for payment in federal_withholding_payments:
			self.increment(self.Metrics.FEDERAL_WITHHOLDING_RECORD_COUNT)
			Payment_containers.append(payment)

		for payment in state_withholding_payments:
			self.increment(self.Metrics.STATE_WITHHOLDING_RECORD_COUNT)
			Payment_containers.append(payment)
		return Payment_containers



	def _get_payments_for_federal_withholding(self,db_session: db.Session) -> List[Payment]:
		logger.info("### :begin - get_all_latest_state_logs_in_end_state FEDERAL_WITHHOLDING_READY_FOR_PROCESSING")
		state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
		associated_class=state_log_util.AssociatedClass.PAYMENT,
		end_state = State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING,
		db_session=db_session,
	 )
		return  [state_log.payment for state_log in state_logs]


	def _get_payments_for_state_withholding(self,db_session: db.Session) -> List[Payment] :
		state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
		associated_class=state_log_util.AssociatedClass.PAYMENT,
		end_state = State.STATE_WITHHOLDING_READY_FOR_PROCESSING,
		db_session=db_session,
	 )
		return  [state_log.payment for state_log in state_logs]


	def is_withholding_records_have_duplicate_records(self,
		db_session: db.Session,payment: Payment, fineos_absence_id : str

		#join and group by state log latest state id
	) -> bool:
		num_payments_query = (
			self.db_session.query(
				Claim.fineos_absence_id,
				Payment.period_start_date,
				Payment.period_end_date,
				Payment.payment_date,
				Payment.amount,
				Payment.fineos_extraction_date,
				func.count(Payment.amount).label("records_count")
			)
				.join(Claim, Payment.claim_id == Claim.claim_id)
				.filter(Claim.claim_id == payment.claim_id)
				.filter(Claim.fineos_absence_id == fineos_absence_id)
				# .filter(Payment.fineos_extraction_date == payment.fineos_extraction_date)
				.group_by(
				Claim.fineos_absence_id,
				Payment.period_start_date,
				Payment.period_end_date,
				Payment.payment_date,
				Payment.amount,
				Payment.fineos_extraction_date)
				#.all()
				.subquery()
		)
		logger.info(num_payments_query)
		items = (self.db_session.query(num_payments_query)
				.filter(num_payments_query.c.records_count > 1).all())
		logger.info(items)
		logger.info(len(items) > 0)
		# logger.info(self.db_session.query(num_payments_query)
		# .filter(num_payments_query.c.records_count[0] > 1))
		return (
			len(items) > 0
			# self.db_session.query(num_payments_query)
			# .filter(num_payments_query.c.records_count[0] > 1)
		)


	#check only date comparison , exculding time
	def _get_primary_payment_record(self,
		db_session: db.Session, payment:Payment
	) -> str:
		primary_payment_id :str
		payment_records = (
			db_session.query(Payment)
			.filter(Payment.claim_id == payment.claim_id)
			.filter(Payment.fineos_extraction_date == payment.fineos_extraction_date)
			.all()
		)
		logger.info(payment_records)
		for p in payment_records:
			payment_end_state_id = (
				db_session.query(StateLog.end_state_id,StateLog)
				.filter(StateLog.payment_id == p.payment_id)
				.filter(StateLog.started_at == p.fineos_extraction_date)
				).order_by(StateLog.created_at.desc()).first()

			if(payment_end_state_id not in [State.STATE_WITHHOLDING_READY_FOR_PROCESSING,
											State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING,
											State.STATE_WITHHOLDING_PENDING_AUDIT,
											State.FEDERAL_WITHHOLDING_PENDING_AUDIT]):
				primary_payment_id = p.payment_id
			return primary_payment_id