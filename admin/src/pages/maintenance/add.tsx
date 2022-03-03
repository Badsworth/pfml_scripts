import "react-datetime/css/react-datetime.css";

//import { Flag, HttpError, patchFlagsByName } from "../../api";
import {
  Field,
  FieldHookConfig,
  Formik,
  FormikErrors,
  FormikProps,
  useField,
  useFormikContext,
} from "formik";
import React, { useRef } from "react";

import Breadcrumb from "../../components/Breadcrumb";
import Datetime from "react-datetime";
import { Helmet } from "react-helmet-async";
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
  const calInput = useRef<HTMLInputElement>(null);

  const calIconClick = () => {
    if (calInput.current) {
      calInput.current.focus();
      calInput.current.click();
    }
  };

  // Declared as any in react-datetime.
  const renderInput = (options: any) => {
    // There is a warning just because this function is called in
    // https://github.com/arqex/react-datetime/blob/7e30d6c20cd864bf8e91bc94e6c3a0ee02864d19/src/DateTime.js#L524
    return (
      <>
        <input {...options} ref={calInput} />
        <i
          className="maintenance-configure__calendar-icon"
          aria-hidden="true"
          tabIndex={-1}
          onClick={calIconClick}
        ></i>
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

  const onSubmitHandler = async (
    values: FormValues /*{ setSubmitting, setFieldError }*/,
  ) => {
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
