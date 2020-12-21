/**
 * Next.js supports IE11. It adds polyfills as they need:
 * https://github.com/zeit/next.js/blob/canary/packages/next-polyfill-nomodule/src/index.js
 *
 * But Next.js cannot add polyfills for code inside NPM modules. So sometimes,
 * you need to add polyfills by yourself.
 * @see https://github.com/zeit/next.js/tree/master/examples/with-polyfills
 */

// `Uint32Array.from` in the @aws-crypto library, which is
// a dependency of Amplify and breaks IE11 when not polyfilled
import "core-js/features/typed-array/from";

// URLSearchParams
import "core-js/features/url-search-params";
