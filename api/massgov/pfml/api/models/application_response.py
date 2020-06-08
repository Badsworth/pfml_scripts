from massgov.pfml.util.converters import json_to_obj


class ApplicationResponse:
    def __init__(self, application, leave_details_schedule=None, payment_preferences=None):
        self.application = application
        self.leave_details_schedule = leave_details_schedule
        self.payment_preferences = payment_preferences

    def create_full_response(self):
        application_json = json_to_obj.get_json_from_object(self.application)

        if application_json is None:
            return None

        leave_details_schedule_json = json_to_obj.get_json_from_object(self.leave_details_schedule)
        payment_prefs_json = json_to_obj.get_json_from_object(self.payment_preferences)

        if leave_details_schedule_json is not None:
            application_json["leave_details"] = self.format_leave_details(
                application_json, leave_details_schedule_json
            )

        if self.application.leave_type_id:
            application_json["leave_type"] = self.application.leave_type.leave_type_description

        if self.application.status_id:
            application_json["status"] = self.application.status.status_description

        # Remove DB attributes not in response or in other components.
        application_json.pop("leave_type_id", None)
        application_json.pop("leave_reason_id", None)
        application_json.pop("leave_reason_qualifier_id", None)
        application_json.pop("status_id", None)
        application_json.pop("relationship_to_caregiver_id", None)
        application_json.pop("relationship_qualifier_id", None)
        application_json.pop("employer_notified", None)
        application_json.pop("employer_notification_date", None)
        application_json.pop("employer_notification_method_id", None)
        application_json.pop("start_time", None)
        application_json.pop("updated_time", None)
        application_json.pop("completed_time", None)
        application_json.pop("submitted_time", None)
        application_json.pop("fineos_absence_id", None)
        application_json.pop("fineos_notification_case_id", None)
        application_json.pop("occupation_id", None)

        if payment_prefs_json is not None:
            application_json["payment_preference"] = payment_prefs_json

        return application_json

    def format_leave_details(self, application_json, leave_details_schedule_json):
        if self.leave_details_schedule.__name__ == "ContinuousLeavePeriod":
            leave_details_schedule_name = "continuous_leave_periods"
        elif self.leave_details_schedule.__name__ == "IntermittentLeavePeriod":
            leave_details_schedule_name = "intermittent_leave_periods"
        else:
            leave_details_schedule_name = "reduced_schedule_leave_periods"

        leave_details_json = {}
        if self.application.occupation_id is not None:
            leave_details_json["leave_reason"] = self.application.occupation.occupation_description

        if self.application.leave_reason_qualifier_id is not None:
            leave_details_json[
                "leave_reason_qualifier"
            ] = self.application.leave_reason_qualifier.leave_reason_qualifier_description

        if self.application.relationship_to_caregiver_id is not None:
            leave_details_json[
                "relationship_to_caregiver"
            ] = self.application.relationship_to_caregiver.relationship_to_caregiver_description

        if self.application.relationship_qualifier_id is not None:
            leave_details_json[
                "relationship_qualifier"
            ] = self.application.relationship_qualifier.relationship_qualifier_description

        if application_json["employer_notified"] is not None:
            leave_details_json["employer_notified"] = application_json["employer_notified"]

        if application_json["employer_notification_date"] is not None:
            leave_details_json["employer_notification_date"] = application_json[
                "employer_notification_date"
            ]

        if self.application.employer_notification_method_id is not None:
            leave_details_json[
                "employer_notification_method"
            ] = self.application.employer_notification_method.notification_method_description

        if leave_details_schedule_json is not None:
            leave_details_json[leave_details_schedule_name] = leave_details_schedule_json

        return leave_details_json
