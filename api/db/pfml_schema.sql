-- Drop tables

DROP TABLE IF EXISTS public.claim;
DROP TABLE IF EXISTS public.link_authorized_rep_employee;
DROP TABLE IF EXISTS public.link_employee_address;
DROP TABLE IF EXISTS public.link_employer_address;
DROP TABLE IF EXISTS public.link_health_care_provider_address;
DROP TABLE IF EXISTS public.health_care_provider;
DROP TABLE IF EXISTS public.link_user_role;
DROP TABLE IF EXISTS public.employer cascade;
DROP TABLE IF EXISTS public.employee cascade;
DROP TABLE IF EXISTS public.lk_status cascade;
DROP TABLE IF EXISTS public.payment_information;
DROP TABLE IF EXISTS public."user";
DROP TABLE IF EXISTS public.wage_and_contribution;
DROP TABLE IF EXISTS public.authorized_representative;
DROP TABLE IF EXISTS public.address;
DROP TABLE IF EXISTS public.lk_address_type;
DROP TABLE IF EXISTS public.lk_geo_state;
DROP TABLE IF EXISTS public.lk_country;
DROP TABLE IF EXISTS public.lk_claim_type;
DROP TABLE IF EXISTS public.lk_race;
DROP TABLE IF EXISTS public.lk_marital_status;
DROP TABLE IF EXISTS public.lk_gender;
DROP TABLE IF EXISTS public.lk_occupation;
DROP TABLE IF EXISTS public.lk_education_level;
DROP TABLE IF EXISTS public.lk_role;
DROP TABLE IF EXISTS public.lk_payment_type;

-- Create tables

CREATE TABLE public.lk_address_type (
	address_type uuid NOT NULL,
	address_description text NOT NULL,
	CONSTRAINT lk_address_type_pk PRIMARY KEY (address_type)
);

CREATE TABLE public.lk_geo_state (
	state_type uuid NOT NULL,
	state_description text NOT NULL,
	CONSTRAINT state_type_pk PRIMARY KEY (state_type)
);

CREATE TABLE public.lk_country (
	country_type uuid NOT NULL,
	country_description text NOT NULL,
	CONSTRAINT country_type_pk PRIMARY KEY (country_type)
);

CREATE TABLE public.lk_claim_type (
	claim_type uuid NOT NULL,
	claim_type_description text NOT NULL,
	CONSTRAINT lk_claim_type_pk PRIMARY KEY (claim_type)
);

CREATE TABLE public.lk_race (
	race_type uuid NOT NULL,
	race_description text NOT NULL,
	CONSTRAINT lk_race_type_pk PRIMARY KEY (race_type)
);

CREATE TABLE public.lk_marital_status (
	marital_status_type uuid NOT NULL,
	marital_status_description text NOT NULL,
	CONSTRAINT lk_marital_status_type_pk PRIMARY KEY (marital_status_type)
);

CREATE TABLE public.lk_gender (
	gender_type uuid NOT NULL,
	gender_description text NOT NULL,
	CONSTRAINT lk_gender_type_pk PRIMARY KEY (gender_type)
);

CREATE TABLE public.lk_occupation (
	occupation_type uuid NOT NULL,
	occupation_description text NOT NULL,
	CONSTRAINT lk_occupation_type_pk PRIMARY KEY (occupation_type)
);

CREATE TABLE public.lk_education_level (
	education_level_type uuid NOT NULL,
	education_level_description text NOT NULL,
	CONSTRAINT lk_education_level_type_pk PRIMARY KEY (education_level_type)
);

CREATE TABLE public.lk_role (
	role_type uuid NOT NULL,
	role_description text NOT NULL,
	CONSTRAINT lk_role_type_pk PRIMARY KEY (role_type)
);

CREATE TABLE public.lk_payment_type (
	payment_type uuid NOT NULL,
	payment_type_description text NOT NULL,
	CONSTRAINT lk_payment_type_pk PRIMARY KEY (payment_type)
);

CREATE TABLE public.lk_status (
	status_type uuid NOT NULL,
	status_description text NOT NULL,
	CONSTRAINT lk_status_type_pk PRIMARY KEY (status_type)
);

CREATE TABLE public.authorized_representative (
	authorized_representative_id uuid NOT NULL,
	first_name text NOT NULL,
	last_name text NOT NULL,
	CONSTRAINT authorized_representative_pk PRIMARY KEY (authorized_representative_id)
);

CREATE TABLE public.health_care_provider (
	health_care_provider_id uuid NOT NULL,
	provider_name text NOT NULL,
	CONSTRAINT health_care_provider_pk PRIMARY KEY (health_care_provider_id)
);

CREATE TABLE public.employer (
	employer_id uuid NOT NULL,
	employer_fein int4 NOT NULL,
	employer_dba text NULL,
	CONSTRAINT employer_pk PRIMARY KEY (employer_id)
);

CREATE TABLE public.payment_information (
	payment_info_id uuid NOT NULL,
	payment_type uuid NOT NULL,
	bank_routing_nbr int4 NULL,
	bank_account_nbr int4 NULL,
	gift_card_nbr int4 NULL,
	CONSTRAINT payment_information_pk PRIMARY KEY (payment_info_id),
	CONSTRAINT payment_information_lk_payment_type_fk FOREIGN KEY (payment_type) REFERENCES lk_payment_type(payment_type)
);

CREATE TABLE public.employee (
	employee_id uuid NOT NULL,
	tax_identifier_id int4 NOT NULL,
	first_name text NOT NULL,
	middle_name text NULL,
	last_name text NOT NULL,
	email_address text NULL,
	phone_number text NULL,
	preferred_comm_method_type text NULL,
	payment_info_id uuid NULL,
	date_of_birth date NULL,
	race_type uuid NULL,
	marital_status_type uuid NULL,
	gender_type uuid NULL,
	occupation_type uuid NULL,
	education_level_type uuid NULL,
	CONSTRAINT employee_pk PRIMARY KEY (employee_id),
	CONSTRAINT employee_lk_education_level_type_fk FOREIGN KEY (education_level_type) REFERENCES lk_education_level(education_level_type),
	CONSTRAINT employee_lk_gender_type_fk FOREIGN KEY (gender_type) REFERENCES lk_gender(gender_type),
	CONSTRAINT employee_lk_marital_status_type_fk FOREIGN KEY (marital_status_type) REFERENCES lk_marital_status(marital_status_type),
	CONSTRAINT employee_lk_occupation_type_fk FOREIGN KEY (occupation_type) REFERENCES lk_occupation(occupation_type),
	CONSTRAINT employee_lk_race_type_fk FOREIGN KEY (race_type) REFERENCES lk_race(race_type),
	CONSTRAINT employee_payment_information_fk FOREIGN KEY (payment_info_id) REFERENCES payment_information(payment_info_id)
);

CREATE TABLE public.claim (
	claim_id uuid NOT NULL,
	employee_id uuid NOT NULL,
	employer_id uuid NOT NULL,
	authorized_representative_id uuid NULL,
	claim_type uuid NOT NULL,
	benefit_amount decimal(6, 2) NOT NULL,
	benefit_days int4 NOT NULL,
	CONSTRAINT claim_pk PRIMARY KEY (claim_id),
	CONSTRAINT claim_authorized_representative_fk FOREIGN KEY (authorized_representative_id) REFERENCES authorized_representative(authorized_representative_id),
	CONSTRAINT claim_employee_fk FOREIGN KEY (employee_id) REFERENCES employee(employee_id),
	CONSTRAINT claim_lk_claim_type_fk FOREIGN KEY (claim_type) REFERENCES lk_claim_type(claim_type)
);

CREATE TABLE public.link_authorized_rep_employee (
	authorized_representative_id uuid NOT NULL,
	employee_id uuid NOT NULL,
	CONSTRAINT link_authorized_rep_employee_authorized_representative_fk FOREIGN KEY (authorized_representative_id) REFERENCES authorized_representative(authorized_representative_id),
	CONSTRAINT link_authorized_rep_employee_employee_fk FOREIGN KEY (employee_id) REFERENCES employee(employee_id)
);

CREATE TABLE public.address (
	address_id uuid NOT NULL,
	address_type uuid NOT NULL,
	address_line_one text NOT NULL,
	address_line_two text NULL,
	city text NOT NULL,
	state_type uuid NOT NULL,
	zip_code int4 NOT NULL,
	country_type uuid NOT NULL,
	CONSTRAINT address_pk PRIMARY KEY (address_id),
	CONSTRAINT address_lk_address_type_fk FOREIGN KEY (address_type) REFERENCES lk_address_type(address_type),
	CONSTRAINT address_lk_country_type_fk FOREIGN KEY (country_type) REFERENCES lk_country(country_type),
	CONSTRAINT address_lk_state_type_fk FOREIGN KEY (state_type) REFERENCES lk_geo_state(state_type)
);

CREATE TABLE public.link_employee_address (
	employee_id uuid NOT NULL,
	address_id uuid NOT NULL,
	CONSTRAINT link_employee_address_address_fk FOREIGN KEY (address_id) REFERENCES address(address_id),
	CONSTRAINT link_employee_address_employee_fk FOREIGN KEY (employee_id) REFERENCES employee(employee_id)
);


CREATE TABLE public.link_employer_address (
	employer_id uuid NOT NULL,
	address_id uuid NOT NULL,
	CONSTRAINT link_employer_address_address_fk FOREIGN KEY (address_id) REFERENCES address(address_id),
	CONSTRAINT link_employer_address_employer_fk FOREIGN KEY (employer_id) REFERENCES employer(employer_id)
);

CREATE TABLE public.link_health_care_provider_address (
	health_care_provider_id uuid NOT NULL,
	address_id uuid NOT NULL,
	CONSTRAINT link_health_care_provider_address_address_fk FOREIGN KEY (address_id) REFERENCES address(address_id),
	CONSTRAINT link_health_care_provider_address_health_care_provider_fk FOREIGN KEY (health_care_provider_id) REFERENCES health_care_provider(health_care_provider_id)
);

CREATE TABLE public."user" (
	user_id uuid NOT NULL,
	active_directory_id text NOT NULL,
	status_type uuid NOT NULL,
	CONSTRAINT user_pk PRIMARY KEY (user_id),
	CONSTRAINT user_lk_status_type_fk FOREIGN KEY (status_type) REFERENCES lk_status(status_type)
);

CREATE TABLE public.link_user_role (
	user_id uuid NOT NULL,
	related_role_id uuid NOT NULL,
	role_type uuid NOT NULL,
	CONSTRAINT link_user_role_lk_role_type_fk FOREIGN KEY (role_type) REFERENCES lk_role(role_type),
	CONSTRAINT link_user_role_user_fk FOREIGN KEY (user_id) REFERENCES "user"(user_id)
);

CREATE TABLE public.wage_and_contribution (
	wage_and_contribution_id uuid NOT NULL,
	account_key text NOT NULL,
	filing_period date NOT NULL,
	employee_id uuid NOT NULL,
	employer_id uuid NOT NULL,
	is_independent_contractor bool NOT NULL,
	is_opted_in bool NOT NULL,
	employer_ytd_wages decimal(20, 2) NOT NULL,
	employer_qtr_wages decimal(20, 2) NOT NULL,
	employer_med_contribution decimal(20, 2) NOT NULL,
	employee_med_contribution decimal(20, 2) NOT NULL,
	employer_fam_contribution decimal(20, 2) NOT NULL,
	employee_fam_contribution decimal(20, 2) NOT NULL,
	CONSTRAINT wage_and_contribution_pk PRIMARY KEY (wage_and_contribution_id),
	CONSTRAINT wage_and_contribution_employee_fk FOREIGN KEY (employee_id) REFERENCES employee(employee_id),
	CONSTRAINT wage_and_contribution_employer_fk FOREIGN KEY (employer_id) REFERENCES employer(employer_id)
);
