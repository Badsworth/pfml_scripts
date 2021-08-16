/**
 * Next.js supports IE11. It adds polyfills as they need:
 * https://github.com/zeit/next.js/blob/canary/packages/next-polyfill-nomodule/src/index.js
 *
 * But Next.js cannot add polyfills for code inside NPM modules. So sometimes,
 * you need to add polyfills by yourself.
 * @see https://github.com/zeit/next.js/tree/master/examples/with-polyfills
 */

// globalThis - not auto-polyfilled by Next.js
import "core-js/stable/global-this";

// `Uint32Array.from` in the @aws-crypto library, which is
// a dependency of Amplify and breaks IE11 when not polyfilled
import "core-js/stable/typed-array/from";

// URLSearchParams
import "core-js/stable/url-search-params";
