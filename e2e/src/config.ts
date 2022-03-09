import { config as dotenv } from "dotenv";
import fileConfiguration from "../config.json";

// Load variables from .env. This populates process.env with .env file values.
// .env files only exist in local environments. In CI, we populate real env variables.
dotenv();

/**
 * Our configuration system determines the proper value for a given property.
 *
 * It operates in "layers", where the "layers" are ordered, and earlier layers override later ones.
 * The layers are:
 * * Values set in Environment variables, either in .env or directly set.
 * * Values from the environment in config.json.
 * * Default values.
 */

/**
 * The raw environment layer is a special layer.  This layer defines every configuration key the system
 * knows about.  It is also the only layer that's allowed to have "undefined" values, which we strip
 * off later on.  We explicitly map this layer's keys to process.env values, because having this
 * explicit mapping allows for the Webpack Environment Plugin to replace these values directly with
 * their string equivalent at compile time. This allows us to effectively "hard code" those values,
 * which would otherwise be lost or inaccessible when the compiled script is run in Flood or Cypress.
 */
function getRawEnvironment() {
  return {
    ENVIRONMENT: process.env.E2E_ENVIRONMENT,
    PORTAL_BASEURL: process.env.E2E_PORTAL_BASEURL,
    PORTAL_PASSWORD: process.env.E2E_PORTAL_PASSWORD,
    PORTAL_USERNAME: process.env.E2E_PORTAL_USERNAME,
    EMPLOYER_PORTAL_PASSWORD: process.env.E2E_EMPLOYER_PORTAL_PASSWORD,

    COGNITO_POOL: process.env.E2E_COGNITO_POOL,
    COGNITO_CLIENTID: process.env.E2E_COGNITO_CLIENTID,

    API_BASEURL: process.env.E2E_API_BASEURL,
    API_FINEOS_CLIENT_ID: process.env.E2E_API_FINEOS_CLIENT_ID,
    API_FINEOS_CLIENT_SECRET: process.env.E2E_API_FINEOS_CLIENT_SECRET,

    FINEOS_BASEURL: process.env.E2E_FINEOS_BASEURL,
    FINEOS_USERNAME: process.env.E2E_FINEOS_USERNAME,
    FINEOS_PASSWORD: process.env.E2E_FINEOS_PASSWORD,
    FINEOS_USERS: process.env.E2E_FINEOS_USERS,

    SSO_USERNAME: process.env.E2E_SSO_USERNAME,
    SSO_PASSWORD: process.env.E2E_SSO_PASSWORD,
    SSO2_USERNAME: process.env.E2E_SSO2_USERNAME,
    SSO2_PASSWORD: process.env.E2E_SSO2_PASSWORD,

    TESTMAIL_APIKEY: process.env.E2E_TESTMAIL_APIKEY,
    TESTMAIL_NAMESPACE: process.env.E2E_TESTMAIL_NAMESPACE,

    EMPLOYEES_FILE: process.env.E2E_EMPLOYEES_FILE,
    EMPLOYERS_FILE: process.env.E2E_EMPLOYERS_FILE,

    LST_EMPLOYEES_FILE: process.env.E2E_LST_EMPLOYEES_FILE,
    LST_EMPLOYERS_FILE: process.env.E2E_LST_EMPLOYERS_FILE,

    ORGUNIT_EMPLOYEES_FILE: process.env.ORGUNIT_EMPLOYEES_FILE,
    ORGUNIT_EMPLOYERS_FILE: process.env.ORGUNIT_EMPLOYERS_FILE,

    HAS_FINEOS_JANUARY_RELEASE: process.env.HAS_FINEOS_JANUARY_RELEASE,

    NEWRELIC_APIKEY: process.env.E2E_NEWRELIC_APIKEY,
    NEWRELIC_ACCOUNTID: process.env.E2E_NEWRELIC_ACCOUNTID,
    NEWRELIC_INGEST_KEY: process.env.E2E_NEWRELIC_INGEST_KEY,

    DOR_IMPORT_URI: process.env.E2E_DOR_IMPORT_URI,
    DOR_ETL_ARN: process.env.E2E_DOR_ETL_ARN,

    TWILIO_ACCOUNTSID: process.env.E2E_TWILIO_ACCOUNTSID,
    TWILIO_AUTHTOKEN: process.env.E2E_TWILIO_AUTHTOKEN,
    TWILIO_NUMBERS: process.env.E2E_TWILIO_NUMBERS,

    FINEOS_HAS_UPDATED_WITHHOLDING_SELECTION:
      process.env.FINEOS_HAS_UPDATED_WITHHOLDING_SELECTION,
    HAS_ORGUNITS_SETUP: process.env.HAS_ORGUNITS_SETUP,
    HAS_LARGE_FILE_COMPRESSION: process.env.HAS_LARGE_FILE_COMPRESSION,
    HAS_EMPLOYER_REIMBURSEMENTS: process.env.HAS_EMPLOYER_REIMBURSEMENTS,
    HAS_APRIL_UPGRADE: process.env.HAS_APRIL_UPGRADE,
    HAS_FEB_RELEASE: process.env.HAS_FEB_RELEASE,
    LST_FILE_RANGE: process.env.E2E_LST_FILE_RANGE, // valid values are "small", "large", "full_range"
    MFA_ENABLED: process.env.MFA_ENABLED,
    S3_INTELLIGENCE_TOOL_BUCKET: process.env.E2E_S3_INTELLIGENCE_TOOL_BUCKET,
    HAS_CHANNEL_SWITCHING: process.env.HAS_CHANNEL_SWITCHING,
    HAS_UPDATED_ER_DASHBOARD: process.env.E2E_HAS_UPDATED_ER_DASHBOARD,
  };
}

type Configuration = Record<
  keyof ReturnType<typeof getRawEnvironment>,
  string | undefined
>;
export type ConfigFactory = (env: string) => {
  get: ConfigFunction;
  configuration: Partial<Configuration>;
};
export type ConfigFunction = (name: keyof Configuration) => string;

/**
 * Returns a new configuration function (and config object) for a given environment.
 *
 * @param env
 */
export const factory: ConfigFactory = (env: string) => {
  if (!(env in fileConfiguration)) {
    throw new Error(
      `Requested config for nonexistent environment: ${env}. Make sure this environment is defined in config.json`
    );
  }
  // The file layer is the configuration defined in config.json for this environment.
  const file: Partial<Configuration> =
    env in fileConfiguration
      ? fileConfiguration[env as keyof typeof fileConfiguration]
      : {};

  // The environment layer is the filtered result of the raw environment layer.
  const environment = Object.fromEntries(
    Object.entries(getRawEnvironment()).filter(([, v]) => typeof v === "string")
  );

  // Form the configuration by merging various "layers" together. Each layer may override the previous.
  const configuration = {
    ...fileConfiguration._default, // Defaults
    ...file,
    ...environment,
    // explicitly map the environment we've been passed. Otherwise, ENVIRONMENT always comes from
    // the .env file, which is not correct when we're using an explicit config factory.
    ENVIRONMENT: env,
  };
  const get: ConfigFunction = (name) => {
    const value = configuration[name];
    if (typeof value === "string") {
      return value;
    }
    throw new Error(
      `Failed to get config value for ${name}. This configuration value can be defined underneath the environment as ${name} in config.json, as E2E_${name} in a .env file, or as an environment variable 'E2E_${name}'`
    );
  };
  return { get, configuration };
};

if (!process.env.E2E_ENVIRONMENT) {
  throw new Error(
    `Failed to get config value for ENVIRONMENT. This configuration value can be defined as E2E_ENVIRONMENT in a .env file, or as an environment variable 'E2E_ENVIRONMENT'`
  );
}
const { get, configuration } = factory(process.env.E2E_ENVIRONMENT);

// Default export is a getter() for config values.
export default get;
// We also export the merged configuration for easy access.
export { configuration };
