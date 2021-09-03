import { config as dotenv } from "dotenv";
import configs from "../config.json";

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
    PORTAL_HAS_LA_STATUS_UPDATES: process.env.E2E_PORTAL_HAS_LA_STATUS_UPDATES,

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

    FLOOD_API_TOKEN: process.env.E2E_FLOOD_API_TOKEN,
    LST_EMPLOYEES_FILE: process.env.E2E_LST_EMPLOYEES_FILE,
    LST_EMPLOYERS_FILE: process.env.E2E_LST_EMPLOYERS_FILE,

    NEWRELIC_APIKEY: process.env.E2E_NEWRELIC_APIKEY,
    NEWRELIC_ACCOUNTID: process.env.E2E_NEWRELIC_ACCOUNTID,
    NEWRELIC_INGEST_KEY: process.env.E2E_NEWRELIC_INGEST_KEY,

    HAS_CLAIMANT_STATUS_PAGE: process.env.HAS_CLAIMANT_STATUS_PAGE,
  };
}

type Configuration = Record<keyof ReturnType<typeof getRawEnvironment>, string>;
export type ConfigFunction = (name: keyof Configuration) => string;

// Load variables from .env. This populates process.env with .env file values.
// .env files only exist in local environments. In CI, we populate real env variables.
dotenv();

// The environment layer is the filtered result of the raw environment layer.
const environment = Object.fromEntries(
  Object.entries(getRawEnvironment()).filter(([, v]) => typeof v === "string")
);

// The file layer is the configuration defined in config.json for this environment.
const file: Partial<Configuration> =
  environment.ENVIRONMENT && environment.ENVIRONMENT in configs
    ? configs[environment.ENVIRONMENT as keyof typeof configs]
    : {};

// The default layer is a set of default values which will be used if nothing is set.
const defaults: Partial<Configuration> = {
  PORTAL_HAS_LA_STATUS_UPDATES: "false",
  NEWRELIC_ACCOUNTID: "2837112",
  HAS_CLAIMANT_STATUS_PAGE: "false",
};
export const merged = {
  ...defaults,
  ...file,
  ...environment,
};

const config: ConfigFunction = function (name) {
  const value = merged[name];
  if (typeof value === "string") {
    return value;
  }
  throw new Error(
    `Failed to get config value for ${name}. This configuration value can be defined underneath the environment as ${name} in config.json, as E2E_${name} in a .env file, or as an environment variable 'E2E_${name}'`
  );
};

export default config;
