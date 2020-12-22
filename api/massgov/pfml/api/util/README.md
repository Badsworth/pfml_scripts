# State Log Utility

## Ordinary Usage

### Creating a New State Log
```py
state_log = state_log_util.create_state_log(
    flow=Flow.RETRIEVE_CPS_VENDOR_EXPORT,
    start_state=State.VERIFY_VENDOR_STATUS,
    associated_model=employee, # Can be an employee/payment/reference_file DB object
    db_session=db_session,
    commit=False  # Boolean on whether to commit the state log (defaults to True), set to False if you want to control when commits occur/handle rollbacks
)
```
This should be done as soon as you begin the process.

This does a few things behind the scenes:
1. Creates the state log
2. Sets the new state log as latest
  1. If this is the first state log associated with a payment/employee/reference_file, creates the record.
3. If there was a previous state log, adds a pointer back to it in `prev_state_log` column.

### Finishing a State Log
This should be done as soon as your processing on a dataset is completed
regardless of success or failure (great to put in a finally block!)
```py
state_log_util.finish_state_log(
        state_log=state_log,
        end_state=State.COMPLETE,
        outcome=state_log_util.build_outcome("status message", validation_container),
        db_session=db_session,
    )
```

### Getting ALL Latest State Logs
Use when you're doing processing and want to know what payments/employees
are waiting to be processed for a given state.
```py
state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
  associated_class=state_log_util.AssociatedClass.EMPLOYEE,
  end_state=State.COMPLETE,
  flow=Flow.RETRIEVE.CPS_VENDOR_EXPORT,
  db_session=db_session
)
```
Note that state log objects contain their payment/employee.

### Getting Stuck State Logs
Sometimes state logs are either not being processed/moved to the next step
or continue to fail in the same state due to some issue.
```py
stuck_state_logs = state_log_util.get_state_logs_stuck_in_state(
  associated_class=state_log_util.AssociatedClass.EMPLOYEE,
  end_state=State.COMPLETE,
  flow=Flow.RETRIEVE.CPS_VENDOR_EXPORT,
  days_stuck=10,
  now=datetime_util.utcnow(), # Optional if you want everything compared against the exact same time
  db_session=db_session
)
```