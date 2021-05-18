import configs from "../config.json";
import { config as dotenv } from "dotenv";

/**
 * This file contains the configuration logic shared by E2E test components.
 *
 * It reads from ../config.json, as well as environment variables, giving priority
 * to the environment variables. For detecting the proper "config environment"
 * to use, it uses the `E2E_ENVIRONMENT` environment variable.
 */

interface E2EConfig {
  PORTAL_BASEURL: string;
  COGNITO_POOL: string;
  COGNITO_CLIENTID: string;
  PORTAL_USERNAME: string;
  PORTAL_PASSWORD: string;
  EMPLOYER_PORTAL_PASSWORD: string;
  API_BASEURL: string;
  FINEOS_BASEURL: string;
  FINEOS_USERNAME: string;
  FINEOS_PASSWORD: string;
  TESTMAIL_APIKEY: string;
  TESTMAIL_NAMESPACE: string;
  EMPLOYEES_FILE: string;
  EMPLOYERS_FILE: string;
  ENVIRONMENT: string;
  API_FINEOS_CLIENT_ID: string;
  API_FINEOS_CLIENT_SECRET: string;
  SSO_PASSWORD: string;
  SSO_USERNAME: string;
  HAS_FINEOS_SP: string;
}
interface LSTConfig {
  FLOOD_API_TOKEN: string;
  TESTMAIL_APIKEY: string;
  PORTAL_PASSWORD: string;
  FINEOS_USERS: string;
  FINEOS_PASSWORD: string;
  LST_EMPLOYEES_FILE: string;
  LST_EMPLOYERS_FILE: string;
}

export type E2ELSTConfig = E2EConfig & LSTConfig;

const defaults: Partial<E2ELSTConfig> = {
  HAS_FINEOS_SP: "false",
};

export type E2ELSTConfigFunction = (name: keyof E2ELSTConfig) => string;

export function factory(env: string | undefined): E2ELSTConfigFunction {
  let config: Partial<E2ELSTConfig> = {};
  if (env) {
    if (env in configs) {
      config = configs[env as keyof typeof configs];
    } else {
      throw new Error(`Requested nonexistent environment: ${env}`);
    }
  }

  // This is the function that does the dirty work of fetching config.
  // Priority is given to environment variables first, then config values.
  return function (name) {
    const envValue = process.env[`E2E_${name}`];
    if (typeof envValue === "string") {
      return envValue;
    }
    const configValue = config[name];
    if (typeof configValue === "string") {
      return configValue;
    }
    const defaultValue = defaults[name];
    if (typeof defaultValue === "string") {
      return defaultValue;
    }
    throw new Error(
      `No configuration found for ${name}. You can either set this value as an environment variable E2E_${name}, or you can define it in config.`
    );
  };
}

// Load variables from .env. This populates process.env with .env file values.
// .env files only exist in local environments. In CI, we populate real env variables.
dotenv();

// For most use cases, we'll just use this "default" config callback.
export default factory(process.env.E2E_ENVIRONMENT);
