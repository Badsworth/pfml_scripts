import { http, HttpError } from "./_api";
import { enrichHttpError } from "./errors";

/**
 * This file monkey patches the API methods to catch errors and add some debug information to them
 * before they're thrown.
 *
 * The actual (generated) API code lives in ./_api.ts.
 */
const fetchJson = http.fetchJson;
http.fetchJson = (
  ...args: Parameters<typeof fetchJson>
): ReturnType<typeof fetchJson> => {
  return fetchJson(...args).catch((e) => {
    if (e instanceof HttpError) {
      enrichHttpError(e);
    }
    throw e;
  });
};

export * from "./_api";
