from datetime import datetime
from typing import List

import massgov.pfml.api.app as app
from massgov.pfml.db.models.applications import (
    Application,
    ApplicationPaymentPreference,
    ContinuousLeavePeriod,
    IntermittentLeavePeriod,
    LeaveReason,
    LeaveReasonQualifier,
    NotificationMethod,
    ReducedScheduleLeavePeriod,
    RelationshipQualifier,
    RelationshipToCareGiver,
)
from massgov.pfml.db.models.employees import Occupation, Status
from massgov.pfml.util.converters import json_to_obj


class ApplicationRequest:
    def __init__(self, json_dict, application):
        self.application = application
        self.json_dict = json_dict

    def validate(self):
        errors_and_warnings = []

        # Validate application attributes
        for key in self.json_dict:
            if key == "leave_details" or key == "payment_preferences":
                continue
            print("application: " + key, self.json_dict[key])

        leave_details_msgs = self.validate_leave_details()
        payment_pref_msgs = self.validate_payment_preferences()

        errors_and_warnings.extend(leave_details_msgs)
        errors_and_warnings.extend(payment_pref_msgs)

        return errors_and_warnings

    def validate_leave_details(self):
        errors_and_warnings = []
        leave_details_json = self.json_dict["leave_details"]
        leave_schedule_type = None

        for key, value in leave_details_json.items():
            if (
                key == "continuous_leave_periods"
                or key == "intermittent_leave_periods"
                or key == "reduced_schedule_leave_periods"
            ):
                leave_schedule_type = key
                continue
            print("leave_details: " + key, value)

        leave_schedule_msgs = self.validate_leave_schedule(
            leave_schedule_type, leave_details_json[leave_schedule_type]
        )
        errors_and_warnings.extend(leave_schedule_msgs)

        return errors_and_warnings

    @staticmethod
    def validate_leave_schedule(leave_schedule_type, leave_schedule):
        errors_and_warnings = []  # type: List[str]

        # Assuming one schedule for now. To be improved.
        for key, value in leave_schedule[0].items():
            print(leave_schedule_type + ": " + key, value)

        return errors_and_warnings

    def validate_payment_preferences(self):
        errors_and_warnings = []  # type: List[str]
        payment_preferences_json = self.json_dict["payment_preferences"]

        # To be improved to deal with array
        for key, value in payment_preferences_json[0].items():
            print("payment_preference: " + key, value)

        return errors_and_warnings

    def update(self):
        if self.application is None:
            application = Application()
        else:
            application = self.application

        for key, value in self.json_dict.items():
            if key == "leave_details" or key == "payment_preferences":
                continue
            if key == "occupation":
                occupations = (
                    app.db_session_raw()
                    .query(Occupation)
                    .filter(Occupation.occupation_description == value)
                    .all()
                )
                if len(occupations) > 0:
                    setattr(application, key + "_id", occupations[0].occupation_id)
                continue
            if key == "application_nickname":
                attr_name = "nickname"
            else:
                attr_name = key
            setattr(application, attr_name, value)

        (application, leave_schedule) = self.update_leave_details(application)
        payment_preferences = self.update_payment_preferences()

        application.updated_time = datetime.now()

        app.db_session_raw().add(application)
        app.db_session_raw().add(leave_schedule)
        app.db_session_raw().add(payment_preferences)
        app.db_session_raw().flush()
        app.db_session_raw().commit()

    def update_leave_details(self, application):
        leave_details_json = self.json_dict["leave_details"]
        leave_schedule = None

        for key, value in leave_details_json.items():
            if (
                key == "continuous_leave_periods"
                or key == "intermittent_leave_periods"
                or key == "reduced_schedule_leave_periods"
            ):
                leave_schedule = self.update_leave_schedule(key, value)
            if key == "reason":
                leave_reasons = (
                    app.db_session_raw()
                    .query(LeaveReason)
                    .filter(LeaveReason.leave_reason_description == value)
                    .all()
                )
                if len(leave_reasons) > 0:
                    application["leave_reason_id"] = leave_reasons[0].leave_reason
                continue
            if key == "reason_qualifier":
                leave_reason_qualifiers = (
                    app.db_session_raw()
                    .query(LeaveReasonQualifier)
                    .filter(LeaveReasonQualifier.leave_reason_qualifier_description == value)
                    .all()
                )
                if len(leave_reason_qualifiers) > 0:
                    application["leave_reason_qualifier_id"] = leave_reason_qualifiers[
                        0
                    ].leave_reason_qualifier_id
                continue
            if key == "relationship_to_caregiver":
                relationship_to_caregiver = (
                    app.db_session_raw()
                    .query(RelationshipToCareGiver)
                    .filter(RelationshipToCareGiver.relationship_to_caregiver_description == value)
                    .all()
                )
                if len(relationship_to_caregiver) > 0:
                    application["relationship_to_caregiver_id"] = relationship_to_caregiver[
                        0
                    ].relationship_to_caregiver_id
                continue
            if key == "relationship_qualifier":
                relationship_qualifier = (
                    app.db_session_raw()
                    .query(RelationshipQualifier)
                    .filter(RelationshipQualifier.relationship_qualifier_description == value)
                    .all()
                )
                if len(relationship_qualifier) > 0:
                    application["relationship_qualifier_id"] = relationship_qualifier[
                        0
                    ].relationship_qualifier_id
                continue
            if key == "employer_notification_method":
                notification_method = (
                    app.db_session_raw()
                    .query(NotificationMethod)
                    .filter(NotificationMethod.notification_method_description == value)
                    .all()
                )
                if len(notification_method) > 0:
                    application["employer_notification_method_id"] = notification_method[
                        0
                    ].notification_method
                continue
            setattr(application, key, leave_details_json[key])

        return application, leave_schedule

    @staticmethod
    def update_leave_schedule(schedule_type, leave_schedule):
        # To be improved in next iteration
        leave_schedule_item = leave_schedule[0]
        schedule_status = leave_schedule_item.pop("status", None)
        if schedule_status is not None:
            status = (
                app.db_session_raw()
                .query(Status)
                .filter(Status.status_description == schedule_status)
                .one_or_none()
            )
            if status is not None:
                leave_schedule_item["status_id"] = status.status_id

        if schedule_type == "continuous_leave_period":
            continuous_leave_period = ContinuousLeavePeriod()
            leave_period = json_to_obj.set_object_from_json(
                leave_schedule_item, continuous_leave_period
            )
        elif schedule_type == "intermittent_leave_period":
            intermittent_leave_period = IntermittentLeavePeriod()
            leave_period = json_to_obj.set_object_from_json(
                leave_schedule_item, intermittent_leave_period
            )
        else:
            reduced_schedule_leave_period = ReducedScheduleLeavePeriod()
            leave_period = json_to_obj.set_object_from_json(
                leave_schedule_item, reduced_schedule_leave_period
            )

        return leave_period

    def update_payment_preferences(self):
        payment_preferences_json = self.json_dict["payment_preferences"]
        payment_preference = ApplicationPaymentPreference()

        # To be improved to deal with array
        payment_preference = json_to_obj.set_object_from_json(
            payment_preferences_json[0], payment_preference
        )
        return payment_preference
