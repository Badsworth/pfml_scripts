import Document, { Head, Html, Main, NextScript } from "next/document";
import React from "react";

/**
 * Overrides the default Next.js Document so that we can customize the
 * static HTML markup that is used on every page. We mainly do this so
 * that our New Relic script is loaded before any other JS.
 *
 * The structure of this page is heavily dictated by Next.js.
 * This markup is only ever rendered during the initial export. Do not add
 * application logic in this file. In most cases, you probably want
 * to use _app.js instead.
 *
 * @see https://nextjs.org/docs/advanced-features/custom-document
 */
class MyDocument extends Document {
  render() {
    return (
      <Html>
        <Head>
          {/* New Relic script must be towards the top of the <head> and before our other scripts */}
          <script src="/new-relic.js" />
        </Head>
        <body>
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }
}

export default MyDocument;
