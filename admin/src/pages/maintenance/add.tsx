import "react-datetime/css/react-datetime.css";

//import { Flag, HttpError, patchFlagsByName } from "../../api";
import {
  Field,
  FieldArray,
  FieldHookConfig,
  Formik,
  FormikErrors,
  FormikProps,
  useField,
  useFormikContext,
} from "formik";

import Breadcrumb from "../../components/Breadcrumb";
import Datetime from "react-datetime";
import { Helmet } from "react-helmet-async";
import React from "react";
import { StaticPropsPermissions } from "../../menus";
import { Timezone } from "../index";
import moment from "moment-timezone";
import { useRouter } from "next/router";

// This is the dateTimeFormat that is rendered in the date time input element.
// Date/times are converted to ISO8601 on save.
const dateTimeFormat = "YYYY-MM-DD h:mmA z";

const disablePastDates = (selected: moment.Moment) => {
  return selected.isAfter(moment().subtract(1, "day"));
};

/*
 * The datetime library uses a value of either as tring or moment object.
 *
 * If the datetime is valid it's a moment object. Otherwise, it's a string.
 */
const handleDateTimeChange = (value: string | moment.Moment): string => {
  if (moment.isMoment(value)) {
    return value.format(dateTimeFormat);
  }
  return "";
};

type FormValues = {
  name: string;
  // A string since radio buttons cannot directly be boolean. Nullable so
  // nothing is checked by default.
  start_use_datetime: "true" | "false" | null;
  start_datetime: string;
  end_use_datetime: "true" | "false" | null;
  end_datetime: string;
  checked_page_routes: string[];
  page_routes: string[];
  custom_page_routes: string[];
  custom_page_route: string;
};

const TextField = (props: { label?: string } & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  return (
    <>
      {props.label && (
        <label htmlFor={props.name} className="maintenance-configure__label">
          {props.label}
          {props.required && <span style={{ color: "red" }}>*</span>}
        </label>
      )}
      <Field
        {...field}
        {...props}
        type="text"
        className={`maintenance-configure__input${
          meta.touched && meta.error
            ? " maintenance-configure__input--error"
            : ""
        }`}
      />
      {meta.touched && meta.error ? (
        <div className="maintenance-configure__error">{meta.error}</div>
      ) : null}
    </>
  );
};

const DateTimeField = (props: FieldHookConfig<string>) => {
  const { setFieldValue } = useFormikContext<FormValues>();
  const [field, meta] = useField(props);

  // Declared as any in react-datetime.
  const renderInput = (options: any) => {
    // There is a warning just because this function is called in
    // https://github.com/arqex/react-datetime/blob/7e30d6c20cd864bf8e91bc94e6c3a0ee02864d19/src/DateTime.js#L524
    return (
      <>
        <input {...options} />
        <i className="maintenance-configure__calendar-icon"></i>
        {meta.error ? (
          <div className="maintenance-configure__error">{meta.error}</div>
        ) : null}
      </>
    );
  };
  return (
    <Datetime
      locale="en"
      {...field}
      isValidDate={disablePastDates}
      dateFormat="YYYY-MM-DD"
      timeFormat="h:mmA z"
      displayTimeZone={Timezone}
      initialViewDate={new Date()}
      renderInput={renderInput}
      value={field.value}
      inputProps={{
        value: field.value,
        name: props.name,
        placeholder: "Choose Date/Time",
        disabled: props.disabled,
        required: props.required,
      }}
      // This overwrites the onChange function from the Formik {..field}.
      onChange={(value) => {
        setFieldValue(props.name, handleDateTimeChange(value));
      }}
      className={`maintenance-configure__datetime maintenance-configure__input${
        meta.error ? " maintenance-configure__input--error" : ""
      }`}
    />
  );
};

/*
 * Error classes are added here if an error is present, but there is
 * currently no validation.
 */
const CheckboxField = (props: { label: string } & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  return (
    <>
      <label className="maintenance-configure__checkbox-label maintenance-configure__label">
        <Field
          type="checkbox"
          {...field}
          {...props}
          className={`maintenance-configure__input${
            meta.touched && meta.error
              ? " maintenance-configure__input--error"
              : ""
          }`}
        />
        {props.label}
      </label>
    </>
  );
};

export default function Maintenance() {
  const router = useRouter();

  // Remove when Flag is in ../../api.
  interface Flag {
    start?: string | null;
    end?: string | null;
    name?: string;
    options?: object;
    enabled?: boolean;
  }

  // The query param can be either a string (it occurs once in the URL) or
  // array of strings (it occurs more than once).
  const checked_page_routes = Array.isArray(router.query?.checked_page_routes)
    ? router.query?.checked_page_routes
    : router.query?.checked_page_routes
    ? [router.query?.checked_page_routes?.toString()]
    : [];

  const custom_page_routes = Array.isArray(router.query?.custom_page_routes)
    ? router.query?.custom_page_routes
    : router.query?.custom_page_routes
    ? [router.query?.custom_page_routes.toString()]
    : [];

  const [showAdvanced, setShowAdvanced] = React.useState(
    !!checked_page_routes.length || !!custom_page_routes.length,
  );

  const showAdvancedOnClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setShowAdvanced(!showAdvanced);
  };

  const handleCancelOnClick = (e: React.MouseEvent) => {
    e.preventDefault();
    router.push("/");
  };

  const handleEndUseDatetimeOnClick =
    (props: FormikProps<FormValues>) => (event: React.MouseEvent) => {
      props.setFieldValue("end_datetime", "");
    };

  const handleStartUseDatetimeOnClick =
    (props: FormikProps<FormValues>) => (event: React.MouseEvent) => {
      props.setFieldValue("start_datetime", "");
    };

  // Populate the start and end radio boxes if a query value exists.
  const start_datetime = router.query?.start?.toString() ?? "";
  const end_datetime = router.query?.end?.toString() ?? "";
  const start_use_datetime = (start_datetime && "true") || null;
  const end_use_datetime = (end_datetime && "true") || null;

  const defaultFormValues: FormValues = {
    name: router.query?.name?.toString() ?? "",
    start_use_datetime: start_use_datetime,
    start_datetime: start_datetime,
    end_use_datetime: end_use_datetime,
    end_datetime: end_datetime,
    checked_page_routes: checked_page_routes,
    page_routes: [],
    custom_page_routes: custom_page_routes,
    custom_page_route: "",
  };

  /*
   * Only one validate method is used which has access to all values since the
   * start/end datetimes need to be compared.
   */
  const validate = (values: FormValues) => {
    const errors: FormikErrors<FormValues> = {};
    if (values.start_datetime !== "") {
      const start = moment.tz(values.start_datetime, dateTimeFormat, Timezone);
      if (start.isValid() === false) {
        errors.start_datetime = "Invalid datetime";
      }
    }
    if (values.end_datetime !== "") {
      const end = moment.tz(values.end_datetime, dateTimeFormat, Timezone);
      if (end.isValid() === false) {
        errors.end_datetime = "Invalid datetime";
      }
      if (end.isBefore(moment.tz(Timezone))) {
        errors.end_datetime = "End cannot be in the past";
      }
      if (
        values.start_datetime !== "" &&
        end.isBefore(moment.tz(values.start_datetime, dateTimeFormat, Timezone))
      ) {
        errors.end_datetime = "End cannot be before start";
      }
    }
    return errors;
  };

  const pageRoutesOnInvalidHandler = (e: React.FormEvent) => {
    const element = e.target as HTMLInputElement;
    if (element.validity.valueMissing === true) {
      element.setCustomValidity("Please select one or more page routes.");
    } else {
      element.setCustomValidity("");
    }
  };

  const onSubmitHandler = async (
    values: FormValues /*{ setSubmitting, setFieldError }*/,
  ) => {
    const custom_page_routes = values.custom_page_routes
      .map((i) => i.trim())
      .filter((i) => i.length > 0);
    // Join checked and custom page routes while removing duplicates.
    values.page_routes = Array.from(
      new Set([...values.checked_page_routes, ...custom_page_routes]),
    );
    const flag: Flag = {};
    // TODO is this always enabled from this page?
    flag.enabled = true;
    flag.start =
      values.start_datetime === ""
        ? null
        : moment.tz(values.start_datetime, dateTimeFormat, Timezone).format();
    flag.end =
      values.end_datetime === ""
        ? null
        : moment.tz(values.end_datetime, dateTimeFormat, Timezone).format();
    flag.options = {
      name: values.name,
      page_routes: values.page_routes,
    };
    /*
    patchFlagsByName({ name: "maintenance" }, flag)
    .then(
      () => {
        router.push("/maintenance");
      },
      (e) => {
        if (e instanceof HttpError) {
          const errors =
            (e.data?.errors as { field: string; message: string }[]) ??
            [];
          errors.map((error) => {
            if (error.field in values) {
              setFieldError(error.field, error.message);
            }
          });
        }
      },
    )
    .finally(() => {
      setSubmitting(false);
    });
    */
    // Remove this push when above is uncommented.
    router.push("/?saved=true");
  };

  return (
    <>
      <Breadcrumb text="Back to Maintenance" href="/" />
      <Helmet>
        <title>Maintenance</title>
      </Helmet>

      <h1>{router.query?.action || "Configure New Maintenance"}</h1>

      <div className="maintenance-configure">
        <div className="maintenance-configure__description">
          <p>
            The Portal includes the ability to have maintenance pages that we
            can turn on in case we need to shut down all or part of the website.
            When the times are set, they will be displayed to the user using
            their timezone and localization preferences.
          </p>
        </div>
        <Formik
          validate={validate}
          initialValues={defaultFormValues}
          onSubmit={onSubmitHandler}
        >
          {(props) => {
            return (
              <form
                className="maintenance-configure__form"
                onSubmit={props.handleSubmit}
                autoComplete="off"
              >
                <TextField
                  name="name"
                  placeholder="Enter type of maintenance"
                  pattern="[a-zA-Z0-9 _\-,]+"
                  label="Name"
                  required
                />
                <div className="maintenance-configure__datetimes-wrapper">
                  <fieldset className="maintenance-configure__datetime-wrapper maintenance-configure__fieldset">
                    <legend>
                      Start Date/Time<span style={{ color: "red" }}>*</span>
                    </legend>
                    <label className="maintenance-configure__radio-label maintenance-configure__label">
                      <Field
                        type="radio"
                        name="start_use_datetime"
                        value="false"
                        onClick={handleStartUseDatetimeOnClick(props)}
                        required
                      />
                      Start Now
                    </label>
                    <label className="maintenance-configure__radio-label">
                      <Field
                        type="radio"
                        name="start_use_datetime"
                        value="true"
                      />
                      Schedule
                      <DateTimeField
                        name="start_datetime"
                        disabled={props.values.start_use_datetime === "false"}
                        required={props.values.start_use_datetime === "true"}
                      />
                    </label>
                  </fieldset>
                  <fieldset className="maintenance-configure__datetime-wrapper maintenance-configure__fieldset">
                    <legend>
                      End Date/Time<span style={{ color: "red" }}>*</span>
                    </legend>
                    <label className="maintenance-configure__radio-label maintenance-configure__label">
                      <Field
                        type="radio"
                        name="end_use_datetime"
                        value="false"
                        onClick={handleEndUseDatetimeOnClick(props)}
                        required
                      />
                      No End Date
                    </label>
                    <label className="maintenance-configure__radio-label maintenance-configure__label">
                      <Field
                        type="radio"
                        name="end_use_datetime"
                        value="true"
                      />
                      Schedule
                      <DateTimeField
                        name="end_datetime"
                        disabled={props.values.end_use_datetime === "false"}
                        required={props.values.end_use_datetime === "true"}
                      />
                    </label>
                  </fieldset>
                </div>
                {/* Transform css property, rotate + 90 or - 90*/}
                <div className="maintenance-configure__advanced">
                  <button
                    className={`maintenance-configure__show-advanced maintenance-configure__show-advanced-icon--${
                      showAdvanced ? "open" : "closed"
                    }`}
                    onClick={showAdvancedOnClick}
                  >
                    Advanced
                  </button>
                  {showAdvanced && (
                    <fieldset className="maintenance-configure__fieldset maintenance-configure__fieldset--advanced">
                      <legend>
                        Page Routes<span style={{ color: "red" }}>*</span>
                      </legend>
                      <CheckboxField
                        label="Entire site"
                        name="checked_page_routes"
                        required={
                          props.values.custom_page_routes.length === 0 &&
                          props.values.checked_page_routes.length === 0
                        }
                        onInvalid={pageRoutesOnInvalidHandler}
                        value="/*"
                      />
                      <CheckboxField
                        label="Applications"
                        name="checked_page_routes"
                        value="/applications/*"
                      />
                      <CheckboxField
                        label="Employers"
                        name="checked_page_routes"
                        value="/employers/*"
                      />
                      <CheckboxField
                        label="Create-Account"
                        name="checked_page_routes"
                        value="/*create-account"
                      />
                      <CheckboxField
                        label="Login"
                        name="checked_page_routes"
                        value="/login"
                      />
                      <FieldArray
                        name="custom_page_routes"
                        render={(arrayHelpers) => (
                          <div className="maintenance-configure__containers">
                            {props.values.custom_page_routes.length > 0 &&
                              props.values.custom_page_routes.map(
                                (route, index) => (
                                  <div
                                    key={index}
                                    className="maintenance-configure__container"
                                  >
                                    <TextField
                                      name={`route.${index}`}
                                      value={route}
                                      disabled
                                      className="maintenance-configure__input"
                                    />
                                    <button
                                      className="btn maintenance-configure__btn--page-route"
                                      type="button"
                                      onClick={() => arrayHelpers.remove(index)}
                                    >
                                      X
                                    </button>
                                  </div>
                                ),
                              )}
                            <div className="maintenance-configure__container">
                              <TextField
                                name="custom_page_route"
                                placeholder="Enter custom page route"
                              />
                              <button
                                type="button"
                                className="btn maintenance-configure__btn--page-route"
                                onClick={() => {
                                  const custom_page_route =
                                    arrayHelpers.form.values.custom_page_route.trim();
                                  if (custom_page_route) {
                                    arrayHelpers.push(custom_page_route);
                                    arrayHelpers.form.setFieldValue(
                                      "custom_page_route",
                                      "",
                                    );
                                  }
                                }}
                              >
                                Add
                              </button>
                            </div>
                          </div>
                        )}
                      />
                      {props.errors.page_routes &&
                        props.touched.page_routes && (
                          <div className="input-feedback">
                            {props.errors.page_routes}
                          </div>
                        )}
                    </fieldset>
                  )}
                </div>
                <fieldset className="maintenance-configure__fieldset maintenance-configure__buttons">
                  <button
                    className="maintenance-configure__btn maintenance-configure__btn--cancel btn btn--cancel"
                    type="button"
                    disabled={props.isSubmitting}
                    onClick={handleCancelOnClick}
                  >
                    Cancel
                  </button>
                  <button
                    className="maintenance-configure__btn maintenance-configure__btn--submit btn"
                    type="submit"
                    disabled={props.isSubmitting}
                  >
                    Save
                  </button>
                </fieldset>
              </form>
            );
          }}
        </Formik>
      </div>
    </>
  );
}

export async function getStaticProps(): Promise<StaticPropsPermissions> {
  return {
    props: {
      permissions: ["MAINTENANCE_READ"],
    },
  };
}
