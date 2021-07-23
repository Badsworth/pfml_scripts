import "react-datetime/css/react-datetime.css";
//import { ApiResponse, FlagsResponse, getFlagsByNameLogs } from "../api";
import {
  Field,
  FieldArray,
  FieldHookConfig,
  Formik,
  FormikErrors,
  useField,
} from "formik";
import Datetime from "react-datetime";
import { useRouter } from "next/router";
import { Helmet } from "react-helmet-async";
import Link from "next/link";
import React from "react";
import moment from "moment";

export default function Maintenance() {
  const router = useRouter();

  type FormValues = {
    maintenance_name: string;
    start: string;
    end: string;
    checked_page_routes: string[];
    page_routes: string[];
    custom_page_routes: string[];
    custom_page_route: string;
  };

  // The query param can be either a string (it occurs once in the URL) or
  // array of strings (it occurs more than once). Handle both cases, defaulting
  // to ["/*"].
  const checked_page_routes = Array.isArray(router.query?.checked_page_routes)
    ? router.query?.checked_page_routes
    : [router.query?.checked_page_routes?.toString() || "/*"];

  const custom_page_routes = Array.isArray(router.query?.custom_page_routes)
    ? router.query?.custom_page_routes
    : router.query?.custom_page_routes
    ? [router.query?.custom_page_routes.toString()]
    : [];

  const defaultFormValues: FormValues = {
    maintenance_name: router.query?.maintenance_name?.toString() ?? "",
    start: "",
    end: "",
    checked_page_routes: checked_page_routes,
    page_routes: [],
    custom_page_routes: custom_page_routes,
    custom_page_route: "",
  };

  const disablePastDates = (selected: moment.Moment) => {
    return selected.isAfter(moment().subtract(1, "day"));
  };

  /*
   * The datetime library uses a value of either as tring or moment object.
   *
   * If the datetime is valid it's a moment object. Otherwise, it's a string.
   */
  const handleDateTimeChange = (value: string | moment.Moment): string => {
    if (value instanceof moment) {
      return moment(value).format("YYYY-MM-DD HH:mm:ss");
    }
    return "";
  };

  /*
   * Only one validate method is used which has access to all values since the
   * start/end datetimes need to be compared.
   */
  const validate = (values: FormValues) => {
    const errors: FormikErrors<FormValues> = {};
    if (
      values.maintenance_name !== "" &&
      !/^[A-Z0-9 _\-]+$/i.test(values.maintenance_name)
    ) {
      errors.maintenance_name = "Invalid name format";
    }
    if (values.start !== "") {
      const start = moment(values.start);
      if (start.isValid() === false) {
        errors.start = "Invalid datetime";
      }
      if (start.isBefore(moment())) {
        errors.start = "Start cannot be in the past";
      }
    }
    if (values.end !== "") {
      const end = moment(values.end);
      if (end.isValid() === false) {
        errors.end = "Invalid datetime";
      }
      if (end.isBefore(moment())) {
        errors.end = "End cannot be in the past";
      }
      if (values.start !== "" && end.isBefore(moment(values.start))) {
        errors.end = "End cannot be before start";
      }
    }
    return errors;
  };

  const TextField = (props: { label?: string } & FieldHookConfig<string>) => {
    const [field, meta] = useField(props);
    return (
      <>
        {props.label && (
          <label
            htmlFor={props.name}
            style={{ display: "block" }}
            className="maintenance-configure__label"
          >
            {props.label}
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

  const DateTimeField = (
    props: { label: string } & FieldHookConfig<string>,
  ) => {
    const [field, meta, helpers] = useField(props);
    const { setValue } = helpers;
    const renderInput = (options: any) => {
      return (
        <label className="maintenance-configure__label">
          {props.label}
          <input {...options} />
        </label>
      );
    };
    return (
      <>
        <Datetime
          {...field}
          isValidDate={disablePastDates}
          dateFormat="YYYY-MM-DD"
          timeFormat="HH:mm:ss"
          renderInput={renderInput}
          initialValue={props.value}
          inputProps={{ name: props.name, placeholder: "Choose Date/Time" }}
          // This overwrites the onChange function from the Formik {..field}.
          onChange={(value) => {
            setValue(handleDateTimeChange(value));
          }}
          className={`maintenance-configure__datetime-wrapper maintenance-configure__input${
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

  /*
   * Error classes are added here if an error is present, but there is
   * currently no validation.
   */
  const CheckboxField = (
    props: { label: string } & FieldHookConfig<string>,
  ) => {
    const [field, meta] = useField(props);
    return (
      <>
        <label
          className="maintenance-configure__label"
          style={{ display: "block" }}
        >
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

  const Form = () => (
    <Formik
      validate={validate}
      initialValues={defaultFormValues}
      onSubmit={async (values) => {
        const custom_page_routes = values.custom_page_routes
          .map((i) => i.trim())
          .filter((i) => i.length > 0);
        // Join checked and custom page routes while removing duplicates.
        values.page_routes = Array.from(
          new Set([...values.checked_page_routes, ...custom_page_routes]),
        );
        // TODO submit to API.
        await new Promise((resolve) => setTimeout(resolve, 500));
        alert(JSON.stringify(values, null, 2));
        //router.push("/maintenance");
      }}
    >
      {(props) => {
        return (
          <form
            className="maintenance-configure__form"
            onSubmit={props.handleSubmit}
            autoComplete="off"
          >
            <TextField
              name="maintenance_name"
              placeholder="Enter type of maintenance"
              label="Name"
            />
            <div className="maintenance-configure__datetimes-wrapper">
              <DateTimeField name="start" label="Start Date/Time" />
              <DateTimeField name="end" label="End Date/Time" />
            </div>
            <fieldset className="maintenance-configure__fieldset">
              <legend>Page Routes</legend>
              <CheckboxField
                label="Entire site"
                name="checked_page_routes"
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
                  <div className="maintenance_configure__custom_page_routes_container">
                    {props.values.custom_page_routes.length > 0 &&
                      props.values.custom_page_routes.map((route, index) => (
                        <div
                          key={index}
                          className="maintenance_configure__custom_page_route_container"
                        >
                          <TextField
                            name={`route.${index}`}
                            value={route}
                            disabled
                            className="maintenance-configure__input"
                          />
                          <button
                            type="button"
                            onClick={() => arrayHelpers.remove(index)}
                          >
                            X
                          </button>
                        </div>
                      ))}
                    <div className="maintenance_configure__custom_page_route_container">
                      <TextField name="custom_page_route" />
                      <button
                        type="button"
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
              {props.errors.page_routes && props.touched.page_routes && (
                <div className="input-feedback">{props.errors.page_routes}</div>
              )}
            </fieldset>
            <button
              className="maintenance-configure__btn btn"
              type="button"
              disabled={props.isSubmitting}
            >
              <Link href="/maintenance">
                <a>Cancel</a>
              </Link>
            </button>
            <button
              className="maintenance-configure__btn btn"
              type="submit"
              disabled={props.isSubmitting}
            >
              Submit
            </button>
          </form>
        );
      }}
    </Formik>
  );

  return (
    <>
      <Helmet>
        <title>Maintenance</title>
        <link
          href="https://fonts.googleapis.com/icon?family=Material+Icons"
          rel="stylesheet"
        />
      </Helmet>

      <h1>Maintenance</h1>

      <div className="maintenance-configure">
        <div className="maintenance-configure__description">
          <p>
            The Portal includes the ability to have maintenance pages that we
            can turn on in case we need to shut down all or part of the website.
            When the times are set, they will be displayed to the user using
            their timezone and localization preferences.
          </p>
        </div>
        <Form />
      </div>
    </>
  );
}
