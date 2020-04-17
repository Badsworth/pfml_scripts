from sqlalchemy.dialects.postgresql import UUID

from massgov.pfml.api.db import orm


class AddressType(orm.Model):
    __tablename__ = "lk_address_type"
    address_type = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    address_description = orm.Column(orm.String)


class GeoState(orm.Model):
    __tablename__ = "lk_geo_state"
    state_type = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    state_description = orm.Column(orm.String)


class Country(orm.Model):
    __tablename__ = "lk_country"
    country_type = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    country_description = orm.Column(orm.String)


class ClaimType(orm.Model):
    __tablename__ = "lk_claim_type"
    claim_type = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    claim_type_description = orm.Column(orm.String)


class Race(orm.Model):
    __tablename__ = "lk_race"
    race_type = orm.Column(orm.Integer, primary_key=True)
    race_description = orm.Column(orm.String)


class MaritalStatus(orm.Model):
    __tablename__ = "lk_marital_status"
    marital_status_type = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    marital_status_description = orm.Column(orm.String)


class Gender(orm.Model):
    __tablename__ = "lk_gender"
    gender_type = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    gender_description = orm.Column(orm.String)


class Occupation(orm.Model):
    __tablename__ = "lk_occupation"
    occupation_type = orm.Column(orm.Integer, primary_key=True)
    occupation_description = orm.Column(orm.String)


class EducationLevel(orm.Model):
    __tablename__ = "lk_education_level"
    education_level_type = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    education_level_description = orm.Column(orm.String)


class Role(orm.Model):
    __tablename__ = "lk_role"
    role_type = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    role_description = orm.Column(orm.String)


class PaymentType(orm.Model):
    __tablename__ = "lk_payment_type"
    payment_type = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    payment_type_description = orm.Column(orm.String)


class Status(orm.Model):
    __tablename__ = "lk_status"
    status_type = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    status_description = orm.Column(orm.String)


class AuthorizedRepresentative(orm.Model):
    __tablename__ = "authorized_representative"
    authorized_representative_id = orm.Column(UUID(as_uuid=True), primary_key=True)
    first_name = orm.Column(orm.String)
    last_name = orm.Column(orm.String)
    employees = orm.relationship("AuthorizedRepEmployee", back_populates="authorized_rep")


class HealthCareProvider(orm.Model):
    __tablename__ = "health_care_provider"
    health_care_provider_id = orm.Column(UUID(as_uuid=True), primary_key=True)
    provider_name = orm.Column(orm.String)
    addresses = orm.relationship("HealthCareProviderAddress", back_populates="health_care_provider")


class Employer(orm.Model):
    __tablename__ = "employer"
    employer_id = orm.Column(UUID(as_uuid=True), primary_key=True)
    employer_fein = orm.Column(orm.Integer)
    employer_dba = orm.Column(orm.String)
    addresses = orm.relationship("EmployerAddress", back_populates="employers", lazy="dynamic")


class PaymentInformation(orm.Model):
    __tablename__ = "payment_information"
    payment_info_id = orm.Column(UUID(as_uuid=True), primary_key=True)
    payment_type = orm.Column(orm.Integer, orm.ForeignKey("lk_payment_type.payment_type"))
    bank_routing_nbr = orm.Column(orm.Integer)
    bank_account_nbr = orm.Column(orm.Integer)
    gift_card_nbr = orm.Column(orm.Integer)


class Employee(orm.Model):
    __tablename__ = "employee"
    employee_id = orm.Column(UUID(as_uuid=True), primary_key=True)
    tax_identifier_id = orm.Column(UUID(as_uuid=True))
    first_name = orm.Column(orm.String)
    middle_name = orm.Column(orm.String)
    last_name = orm.Column(orm.String)
    email_address = orm.Column(orm.String)
    phone_number = orm.Column(orm.String)
    preferred_comm_method_type = orm.Column(orm.String)
    payment_info_id = orm.Column(
        UUID(as_uuid=True), orm.ForeignKey("payment_information.payment_info_id")
    )
    date_of_birth = orm.Column(orm.Date)
    race_type = orm.Column(orm.Integer, orm.ForeignKey("lk_race.race_type"))
    marital_status_type = orm.Column(
        orm.Integer, orm.ForeignKey("lk_marital_status.marital_status_type")
    )
    gender_type = orm.Column(orm.Integer, orm.ForeignKey("lk_gender.gender_type"))
    occupation_type = orm.Column(orm.Integer, orm.ForeignKey("lk_occupation.occupation_type"))
    education_level_type = orm.Column(
        orm.Integer, orm.ForeignKey("lk_education_level.education_level_type")
    )
    authorized_reps = orm.relationship(
        "AuthorizedRepEmployee", back_populates="employee", lazy="dynamic"
    )
    addresses = orm.relationship("EmployeeAddress", back_populates="employees", lazy="dynamic")


class Claim(orm.Model):
    __tablename__ = "claim"
    claim_id = orm.Column(UUID(as_uuid=True), primary_key=True)
    employer_id = orm.Column(UUID(as_uuid=True))
    authorized_representative_id = orm.Column(UUID(as_uuid=True))
    claim_type = orm.Column(UUID(as_uuid=True))
    benefit_amount = orm.Column(orm.Numeric(asdecimal=True))
    benefit_days = orm.Column(orm.Integer)


class AuthorizedRepEmployee(orm.Model):
    __tablename__ = "link_authorized_rep_employee"
    authorized_representative_id = orm.Column(
        UUID(as_uuid=True),
        orm.ForeignKey("authorized_representative.authorized_representative_id"),
        primary_key=True,
    )
    employee_id = orm.Column(
        UUID(as_uuid=True), orm.ForeignKey("employee.employee_id"), primary_key=True
    )
    authorized_rep = orm.relationship("AuthorizedRepresentative", back_populates="employees")
    employee = orm.relationship("Employee", back_populates="authorized_reps")


class Address(orm.Model):
    __tablename__ = "address"
    address_id = orm.Column(UUID(as_uuid=True), primary_key=True)
    address_type = orm.Column(orm.Integer, orm.ForeignKey("lk_address_type.address_type"))
    address_line_one = orm.Column(orm.String)
    address_line_two = orm.Column(orm.String)
    city = orm.Column(orm.String)
    state_type = orm.Column(orm.Integer, orm.ForeignKey("lk_geo_state.state_type"))
    zip_code = orm.Column(orm.String)
    country_type = orm.Column(orm.Integer, orm.ForeignKey("lk_country.country_type"))
    employees = orm.relationship("EmployeeAddress", back_populates="addresses", lazy="dynamic")
    employers = orm.relationship("EmployerAddress", back_populates="addresses", lazy="dynamic")
    health_care_providers = orm.relationship("HealthCareProviderAddress", back_populates="address")


class EmployeeAddress(orm.Model):
    __tablename__ = "link_employee_address"
    employee_id = orm.Column(
        UUID(as_uuid=True), orm.ForeignKey("employee.employee_id"), primary_key=True
    )
    address_id = orm.Column(
        UUID(as_uuid=True), orm.ForeignKey("address.address_id"), primary_key=True
    )
    employees = orm.relationship("Employee", back_populates="addresses")
    addresses = orm.relationship("Address", back_populates="employees")


class EmployerAddress(orm.Model):
    __tablename__ = "link_employer_address"
    employer_id = orm.Column(
        UUID(as_uuid=True), orm.ForeignKey("employer.employer_id"), primary_key=True
    )
    address_id = orm.Column(
        UUID(as_uuid=True), orm.ForeignKey("address.address_id"), primary_key=True
    )
    employers = orm.relationship("Employer", back_populates="addresses")
    addresses = orm.relationship("Address", back_populates="employers")


class HealthCareProviderAddress(orm.Model):
    __tablename__ = "link_health_care_provider_address"
    health_care_provider_id = orm.Column(
        UUID(as_uuid=True),
        orm.ForeignKey("health_care_provider.health_care_provider_id"),
        primary_key=True,
    )
    address_id = orm.Column(
        UUID(as_uuid=True), orm.ForeignKey("address.address_id"), primary_key=True
    )
    health_care_provider = orm.relationship("HealthCareProvider", back_populates="addresses")
    address = orm.relationship("Address", back_populates="health_care_providers")


class User(orm.Model):
    __tablename__ = "user"
    user_id = orm.Column(UUID(as_uuid=True), primary_key=True)
    active_directory_id = orm.Column(orm.String)
    status_type = orm.Column(orm.Integer, orm.ForeignKey("lk_status.status_type"))

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])


class UserRole(orm.Model):
    __tablename__ = "link_user_role"
    user_id = orm.Column(UUID(as_uuid=True), orm.ForeignKey("user.user_id"), primary_key=True)
    role_type = orm.Column(orm.Integer, orm.ForeignKey("lk_role.role_type"), primary_key=True)
    related_role_id = orm.Column(UUID(as_uuid=True))


class WageAndContribution(orm.Model):
    __tablename__ = "wage_and_contribution_id"
    wage_and_contribution_id = orm.Column(UUID(as_uuid=True), primary_key=True)
    account_key = orm.Column(orm.String)
    filing_period = orm.Column(orm.Date)
    employee_id = orm.Column(UUID(as_uuid=True), orm.ForeignKey("employee.employee_id"))
    employer_id = orm.Column(UUID(as_uuid=True), orm.ForeignKey("employer.employer_id"))
    is_independent_contractor = orm.Column(orm.Boolean)
    is_opted_in = orm.Column(orm.Boolean)
    employer_ytd_wages = orm.Column(orm.Numeric(asdecimal=True), nullable=False)
    employer_qtr_wages = orm.Column(orm.Numeric(asdecimal=True), nullable=False)
    employer_med_contribution = orm.Column(orm.Numeric(asdecimal=True), nullable=False)
    employer_fam_contribution = orm.Column(orm.Numeric(asdecimal=True), nullable=False)
