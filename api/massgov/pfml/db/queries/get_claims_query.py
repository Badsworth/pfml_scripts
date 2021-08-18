import re
from datetime import date
from enum import Enum
from typing import Any, Callable, List, Optional, Set, Type, Union

from sqlalchemy import Column, and_, asc, desc, func, or_
from sqlalchemy.orm import contains_eager
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.selectable import Alias

from massgov.pfml import db
from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.base import Base
from massgov.pfml.db.models.employees import (
    Claim,
    Employee,
    LkAbsenceStatus,
    ManagedRequirement,
    ManagedRequirementStatus,
    ManagedRequirementType,
    User,
)
from massgov.pfml.util.paginate.paginator import (
    OrderDirection,
    Page,
    PaginationAPIContext,
    page_for_api_context,
)


# Extra Absence Statuses defined in the UI
# enum values for claim_status url param in claims endpoint
class ActionRequiredStatusFilter(str, Enum):
    PENDING = "Pending"
    OPEN_REQUIREMENT = "Open requirement"
    PENDING_NO_ACTION = "Pending - no action"

    @classmethod
    def all(cls):
        return [cls.PENDING, cls.OPEN_REQUIREMENT, cls.PENDING_NO_ACTION]


PendingAbsenceStatuses = ["Intake In Progress", "In Review", "Adjudication", None]

# Wrapper for the DB layer of the `get_claims` endpoint
# Create a query for filtering and ordering Claim results
# The "get" methods are idempotent, the rest will change the query and affect the results


class GetClaimsQuery:
    joined: List[Union[Type[Base], Alias]]

    def __init__(self, db_session: db.Session):
        self.session = db_session
        self.query = db_session.query(Claim)
        self.joined = []

    # prevents duplicate joining of a table
    def join(
        self,
        model: Union[Type[Base], Alias],
        isouter: bool = False,
        join_filter: Optional[Any] = None,
    ) -> None:
        for joined in self.joined:
            if model is joined:
                return
        self.joined.append(model)
        if join_filter is not None:  # use join_filter when query filter would not work
            self.query = self.query.join(model, join_filter, isouter=isouter)
        else:
            self.query = self.query.join(model, isouter=isouter)

    def add_employer_ids_filter(self, employer_ids: List[str]) -> None:
        self.query = self.query.filter(Claim.employer_id.in_(employer_ids))

    # TODO: current_user shouldn't be Optional - `get_claims` should throw an error instead
    def add_user_owns_claim_filter(self, current_user: Optional[User]) -> None:
        filter = Claim.application.has(Application.user_id == current_user.user_id)  # type: ignore
        self.query = self.query.filter(filter)

    def get_managed_requirement_status_filters(self, absence_statuses: Set[str]) -> List[Any]:
        has_pending_no_action = ActionRequiredStatusFilter.PENDING_NO_ACTION in absence_statuses
        has_open_requirement = ActionRequiredStatusFilter.OPEN_REQUIREMENT in absence_statuses
        has_pending = ActionRequiredStatusFilter.PENDING in absence_statuses

        filters = []
        filter = Claim.managed_requirements.any(  # type: ignore
            ManagedRequirement.managed_requirement_status_id
            == ManagedRequirementStatus.OPEN.managed_requirement_status_id
        )
        if has_open_requirement:
            filters.append(filter)
        if has_pending_no_action:
            pending_no_action_filters = [
                or_(
                    LkAbsenceStatus.absence_status_description.in_(PendingAbsenceStatuses),
                    Claim.fineos_absence_status_id.is_(None),
                ),
                ~filter,
            ]
            filters.append(and_(*pending_no_action_filters))
        if has_pending:
            absence_statuses.update(PendingAbsenceStatuses)  # type: ignore

        # remove absence status not in database
        absence_statuses.difference_update(ActionRequiredStatusFilter.all())  # update in place
        return filters

    def add_absence_status_filter(self, absence_statuses: Set[str]) -> None:
        self.join(Claim.fineos_absence_status, isouter=True)  # type:ignore
        filters = self.get_managed_requirement_status_filters(absence_statuses)
        if not len(absence_statuses):
            self.query = self.query.filter(or_(*filters))
            return

        filters.append(LkAbsenceStatus.absence_status_description.in_(absence_statuses))
        if None in absence_statuses:
            filters.append(Claim.fineos_absence_status_id.is_(None))
        self.query = self.query.filter(or_(*filters))

    def employee_search_sub_query(self) -> Alias:
        search_columns = [
            Employee,
            func.concat(Employee.first_name, " ", Employee.last_name).label("first_last"),
            func.concat(Employee.last_name, " ", Employee.first_name).label("last_first"),
            func.concat(
                Employee.first_name, " ", Employee.middle_name, " ", Employee.last_name
            ).label("full_name"),
        ]
        return self.session.query(*search_columns).subquery()

    def format_search_string(self, search_string: str) -> str:
        return re.sub(r"\s+", " ", search_string).strip()

    def add_search_filter(self, search_string: str) -> None:
        self.join(Claim.employee, isouter=True)  # type:ignore
        self.query = self.query.filter(Employee.employee_id == Claim.employee_id)
        search_string = self.format_search_string(search_string)
        search_sub_query = self.employee_search_sub_query()
        self.join(search_sub_query, isouter=True)
        self.query = self.query.filter(search_sub_query.c.employee_id == Claim.employee_id)
        if " " in search_string:
            filters = [
                search_sub_query.c.first_last.ilike(f"%{search_string}%"),
                search_sub_query.c.last_first.ilike(f"%{search_string}%"),
                search_sub_query.c.full_name.ilike(f"%{search_string}%"),
            ]
        else:
            filters = [
                Claim.fineos_absence_id.ilike(f"%{search_string}%"),
                Employee.first_name.ilike(f"%{search_string}%"),
                Employee.middle_name.ilike(f"%{search_string}%"),
                Employee.last_name.ilike(f"%{search_string}%"),
            ]
        self.query = self.query.filter(or_(*filters))

    def add_managed_requirements_filter(self) -> None:
        filters = [
            ManagedRequirement.claim_id == Claim.claim_id,
            ManagedRequirement.managed_requirement_type_id
            == ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
            ManagedRequirement.managed_requirement_status_id
            == ManagedRequirementStatus.OPEN.managed_requirement_status_id,
            ManagedRequirement.follow_up_date >= date.today(),
        ]
        self.join(ManagedRequirement, isouter=True, join_filter=and_(*filters))
        self.query = self.query.options(contains_eager("managed_requirements"))

    def add_order_by(self, context: PaginationAPIContext) -> None:
        is_asc = context.order_direction == OrderDirection.asc.value
        sort_fn = asc_null_first if is_asc else desc_null_last

        if context.order_key is Claim.employee:
            self.add_order_by_employee(sort_fn)

        elif context.order_key is Claim.fineos_absence_status:
            self.add_order_by_absence_status(is_asc)

        elif context.order_by in Claim.__table__.columns:
            self.add_order_by_column(is_asc, context)

    def add_order_by_employee(self, sort_fn: Callable) -> None:
        order_keys = [
            sort_fn(Employee.last_name),
            sort_fn(Employee.first_name),
            sort_fn(Employee.middle_name),
        ]

        self.join(Claim.employee, isouter=True)  # type:ignore
        self.query = self.query.order_by(*order_keys)

    def add_order_by_absence_status(self, is_asc: bool) -> None:
        sort_fn = asc_null_first if is_asc else desc_null_last
        # oldest follow up date first if ascending
        sort_req = asc if is_asc else desc
        self.join(Claim.fineos_absence_status, isouter=True)  # type:ignore
        self.join(Claim.employee, isouter=True)  # type:ignore
        order = [
            sort_req(Claim.soonest_open_requirement_date),  # type:ignore
            sort_fn(LkAbsenceStatus.sort_order),
            sort_fn(Employee.last_name),
        ]
        self.query = self.query.order_by(*order)

    def add_order_by_column(self, is_asc: bool, context: PaginationAPIContext) -> None:
        order_key = context.order_key.asc() if is_asc else context.order_key.desc()
        self.query = self.query.order_by(order_key)

    def get_paginated_results(self, context: PaginationAPIContext) -> Page:
        return page_for_api_context(context, self.query)


def asc_null_first(column: Column) -> UnaryExpression:
    return asc(column).nullsfirst()


def desc_null_last(column: Column) -> UnaryExpression:
    return desc(column).nullslast()
