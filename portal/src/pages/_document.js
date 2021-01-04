import Document, { Head, Html, Main, NextScript } from "next/document";
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
          {/* New Relic script must be towards the top of the <head> and before our other scripts */}
          <script src="/new-relic.js" />

          <script
            dangerouslySetInnerHTML={{
              __html:
                "(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':\n" +
                "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],\n" +
                "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n" +
                `'https://www.googletagmanager.com/gtm.js?id='+i+dl+ '&gtm_auth=${process.env.gtmConfig.auth}&gtm_preview=${process.env.gtmConfig.preview}&gtm_cookies_win=x';f.parentNode.insertBefore(j,f);\n` +
                "})(window,document,'script','dataLayer','GTM-MCLNNQC');",
            }}
          />

          <link href="/favicon.png" rel="shortcut icon" type="image/png" />
          {process.env.BUILD_ENV !== "prod" && (
            <meta name="robots" content="noindex" />
          )}
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
