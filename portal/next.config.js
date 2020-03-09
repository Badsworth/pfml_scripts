const path = require("path");
const resolve = require("resolve");
// The CSS workarounds are to solve conflicts between AWS Amplify CSS and `npm run dev` and `npm run build` commands.
// See https://github.com/aws-amplify/amplify-js/issues/3854#issuecomment-554702182 for context and source of fix.
const withCSS = require("@zeit/next-css");
// Portal uses Sass (and we import the U.S. Web Design System's Sass)
const withSass = require("@zeit/next-sass");
const withFonts = require("next-fonts");

const buildEnv = process.env.BUILD_ENV || "dev";
const envVariables = require("./../infra/portal_config/" + buildEnv);

global.navigator = () => null;

module.exports = withSass(
  withCSS(
    // imported fonts are copied into .next/static/chunks/fonts
    // See https://github.com/rohanray/next-fonts/blob/master/index.js
    withFonts({
      enableSvg: true,
      env: {
        ...envVariables,
      },
      exportTrailingSlash: true,
      sassLoaderOptions: {
        includePaths: [
          path.resolve(__dirname, "node_modules/uswds/dist/scss"),
          path.resolve(__dirname, "node_modules"),
        ],
      },
      webpack(config, options) {
        const { dir, isServer } = options;
        config.externals = [];
        // This modifies what is excluded by Webpack in output bundles to resolve conflicts with @aws-amplify CSS files.
        if (isServer) {
          config.externals.push((context, request, callback) => {
            resolve(
              request,
              { basedir: dir, preserveSymlinks: true },
              (err, res) => {
                if (err) {
                  return callback();
                }
                if (
                  res.match(/node_modules[/\\].*\.css/) &&
                  !res.match(/node_modules[/\\]webpack/) &&
                  !res.match(/node_modules[/\\]@aws-amplify/)
                ) {
                  return callback(null, `commonjs ${request}`);
                }
                callback();
              }
            );
          });
        }
        return config;
      },
    })
  )
);
