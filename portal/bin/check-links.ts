/* eslint-disable no-console */
/**
 * @file Check if any external routes are broken
 * Usage:
 * $ ./node_modules/.bin/tsc bin/check-links.ts --outDir builds/
 * $ node builds/bin/check-links.js
 */
import * as https from "https";
import routes from "../src/routes";

interface BadLink {
  url: string;
  statusCode?: number;
  finalUrl?: string;
}

const badLinks: BadLink[] = [];

/**
 * Send HTTP GET request
 */
function request(url: string): Promise<{ url: string; statusCode?: number }> {
  return new Promise((resolve, reject) => {
    https
      .get(url, async (res) => {
        const { statusCode } = res;

        if (
          statusCode !== undefined &&
          statusCode >= 300 &&
          statusCode < 400 &&
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
 */
async function checkRoutes(routesObj: {
  [routeOrGroupName: string]: string | { [nestedRouteName: string]: string };
}) {
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

checkRoutes(routes.external)
  .then(() => {
    if (badLinks.length) {
      console.log(
        "\n\n⛔️ Some links returned a non-success response. You should check these."
      );
      console.log(badLinks);

      // This sets an output variable that our GitHub Action can use in subsequent steps:
      const badUrls = badLinks.map((link) => `• ${link.url}`).join("%0A"); // %0A is a newline
      console.log(`::set-output name=badUrls::${badUrls}`);

      process.exit(1);
    } else {
      console.log("✅ No bad links");
      process.exit(0);
    }
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
