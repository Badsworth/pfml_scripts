/* eslint-disable no-console promise/catch-or-return */
/**
 * @file Check if any external routes are broken
 * Usage: node bin/check-links.mjs
 */
import "@babel/register"; // transpile routes.js file
import https from "https";
import routes from "../src/routes.js";

const badLinks = [];

/**
 * Send HTTP GET request
 * @param {string} url
 * @returns {Promise<{url: string, statusCode: number}>}
 */
function request(url) {
  return new Promise((resolve, reject) => {
    https
      .get(url, async (res) => {
        const { statusCode } = res;

        if (
          res.statusCode >= 300 &&
          res.statusCode < 400 &&
          res.headers.location
        ) {
          const location = res.headers.location;
          const redirectedTo = new URL(location, url).toString();
          const data = await request(redirectedTo);

          console.log(`↪ ${url}\n    redirected to:\n    ${redirectedTo}`);
          return resolve(data);
        }

        resolve({ statusCode, url });
      })
      .on("error", reject);
  });
}

/**
 * Check if given routes respond with a 200 status code
 * @param {object} routesObj
 * @returns {Promise}
 */
async function checkRoutes(routesObj) {
  const urls = Object.values(routesObj);

  for await (const url of urls) {
    if (typeof url === "object") {
      await checkRoutes(url);
      return;
    }

    const { url: finalUrl, statusCode } = await request(url);
    console.log(statusCode, url);

    if (statusCode !== 200) {
      badLinks.push({ url, statusCode, finalUrl });
    }
  }
}

await checkRoutes(routes.default.external);

if (badLinks.length) {
  console.warn(
    "\n\n⛔️ Some links returned a non-200 status code. You should check these:"
  );
  console.warn(badLinks);
} else {
  console.log("✅ No bad links");
}
