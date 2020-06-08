import Document, { Head, Html, Main, NextScript } from "next/document";
import React from "react";

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
      <Html>
        <Head>
          {/* New Relic script must be towards the top of the <head> and before our other scripts */}
          <script
            dangerouslySetInnerHTML={{
              __html: `
              window.NREUM={};
              window.NREUM.loader_config={
                accountID:"1606654",
                trustKey:"1606654",
                agentID:"${process.env.newRelicAppId}",
                licenseKey:"0c7a02d605",
                applicationID:"${process.env.newRelicAppId}"
              };
              window.NREUM.info={
                beacon:"bam.nr-data.net",
                errorBeacon:"bam.nr-data.net",
                licenseKey:"0c7a02d605",
                applicationID:"${process.env.newRelicAppId}",
                sa:1
              };
            `,
            }}
          />
          <script src="/new-relic.js" />

          <link href="/favicon.png" rel="shortcut icon" type="image/png" />

          {/* Block search engine indexing during development: https://lwd.atlassian.net/browse/CP-458 */}
          <meta name="robots" content="noindex" />
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
