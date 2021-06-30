
from massgov.pfml.fineos import create_client
from pprint import pprint

def init(app):

    @app.route("/fineostest")
    def fineos_test():
        # if not secrets.compare_digest(key, dashboard_password):
            # raise NotFound
        # entries = import_jobs_get()
        print('ehllo')

        fineos = create_client()
        # res = fineos.get_absence_period_decisions(
        user_id="PFML_LEAVE_ADMIN_BF773A0C-6681-46FF-9565-3E39B0ED4019",
        # )
        res = fineos._group_client_api(
            "GET",
            # /groupClient/group-client-users/{groupClientUserId}/edit
            # f"groupClient/absences/absence-period-decisions?absenceId={absence_id}",
            # /groupClient
            f"/groupClient/group-client-users/{user_id}/edit",
            user_id,
            # "get_absence_period_decisions",
        )
        # except exception.FINEOSClientError as error:
        #     logger.error(
        #         "FINEOS Client Exception: get_absence_period_decisions",
        #         extra={"method_name": "get_absence_period_decisions"},
        #         exc_info=error,
        #     )
        #     error.method_name = "get_absence_period_decisions"
        #     raise error
        # absence_periods = response.json()
        # set_empty_dates_to_none(absence_periods, ["startDate", "endDate"])
        # return models.group_client_api.PeriodDecisions.parse_obj(absence_periods)
        pprint(res)
        # return flask.render_template("dashboards.html", data=entries, now=utcnow())
