import { Browser } from "@flood/element";

function makeFetchInit(token: string, init?: RequestInit) {
  return {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "User-Agent": "PFML Load Testing Bot",
      ...init?.headers,
    },
  };
}

/**
 * Perform a browser-based fetch request, sending and receiving JSON.
 */
export function fetchJSON(
  browser: Browser,
  token: string,
  info: RequestInfo,
  init?: RequestInit
): // eslint-disable-next-line @typescript-eslint/no-explicit-any
Promise<any> {
  const url = typeof info === "string" ? info : info.url;
  console.log(`Issuing request to ${url}`);

  return browser.evaluate(
    (info, init) => {
      const url = typeof info === "string" ? info : info.url;
      const method = init.method ?? "GET";
      return fetch(info, init)
        .catch((reason) => {
          // Catch any error that fails fetch entirely and wrap it in a more useful message than "failed to fetch".
          return Promise.reject(
            `Received an unspecified error while executing a fetch request: ${method} ${url}. The original reason was: ${reason}`
          );
        })
        .then((res) => {
          // Catch errors that indicate a failed response and create a useful message from them.
          if (!res.ok) {
            return Promise.reject(
              `Received a ${res.status} ${res.statusText} error while executing a fetch request: ${method} ${url}.`
            );
          }
          return res;
        })
        .then((res) => res.json());
    },
    info,
    makeFetchInit(token, {
      ...init,
      headers: { "Content-Type": "application/json" },
    })
  );
}

type FormDataLike = {
  [k: string]: string | { data: Buffer; type: string; name?: string };
};
/**
 * Perform a browser-based fetch request, sending form data and receiving JSON.
 */
export function fetchFormData(
  browser: Browser,
  token: string,
  data: FormDataLike,
  info: RequestInfo,
  init?: RequestInit
): // eslint-disable-next-line @typescript-eslint/no-explicit-any
Promise<any> {
  return browser.evaluate(
    (info, init, data: FormDataLike) => {
      const body = new FormData();
      Object.entries(data).forEach(([key, value]) => {
        if (typeof value === "string") {
          body.append(key, value);
        } else {
          // @ts-ignore
          const blob = new Blob([Uint8Array.from(value.data.data)], {
            type: value.type,
          });
          body.append(key, blob, value.name);
        }
      });
      const url = typeof info === "string" ? info : info.url;
      const method = init.method ?? "GET";
      return fetch(info, { ...init, body })
        .catch((reason) => {
          // Catch any error that fails fetch entirely and wrap it in a more useful message than "failed to fetch".
          return Promise.reject(
            `Received an unspecified error while executing a fetch request: ${method} ${url}. The original reason was: ${reason}`
          );
        })
        .then((res) => {
          // Catch errors that indicate a failed response and create a useful message from them.
          if (!res.ok) {
            return Promise.reject(
              `Received a ${res.status} ${res.statusText} error while executing a fetch request: ${method} ${url}.`
            );
          }
          return res;
        })
        .then((res) => res.json());
    },
    info,
    makeFetchInit(token, init),
    data
  );
}
