import Document, { Head, Html, Main, NextScript } from "next/document";
import GlobalDocumentHead from "../components/GlobalDocumentHead";
import React from "react";
import UnsupportedBrowserBanner from "../components/UnsupportedBrowserBanner";

/**
 * Overrides the default Next.js Document so that we can customize the
 * static HTML markup that is used on every page.
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
      <Html lang="en-US">
        <Head>
          <GlobalDocumentHead />
        </Head>
        <body>
          <UnsupportedBrowserBanner />
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }
}

export default MyDocument;
