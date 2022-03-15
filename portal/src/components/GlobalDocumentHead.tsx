import React from "react";

/**
 * Global <head> tags. This is a component to better support unit testing, since
 * we had challenges directly testing _document.js, where this gets rendered.
 */
function GlobalDocumentHead() {
  return (
    <React.Fragment>
      {/* New Relic script must be towards the top of the <head> and before our other scripts */}
      <script src="/new-relic.js" />

      <script
        dangerouslySetInnerHTML={{
          __html:
            "(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':\n" +
            "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],\n" +
            "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n" +
            `'https://www.googletagmanager.com/gtm.js?id='+i+dl+ '&gtm_auth=${process.env.gtmConfigAuth}&gtm_preview=${process.env.gtmConfigPreview}&gtm_cookies_win=x';f.parentNode.insertBefore(j,f);\n` +
            "})(window,document,'script','dataLayer','GTM-MCLNNQC');",
        }}
      />

      <link href="/favicon.png" rel="shortcut icon" type="image/png" />
      {process.env.BUILD_ENV !== "prod" && (
        <meta name="robots" content="noindex" />
      )}
    </React.Fragment>
  );
}

export default GlobalDocumentHead;
