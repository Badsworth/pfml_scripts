// babel.config.js
module.exports = {
  plugins: [
    "@babel/plugin-proposal-class-properties",
    // Manually including these plugins because webpack4 has issue with when targeting node 14 and above.
    // Can be resolved by moving to webpack5
    // See @link{https://github.com/webpack/webpack/issues/10227}
    "@babel/plugin-proposal-nullish-coalescing-operator",
    "@babel/plugin-proposal-optional-chaining",
  ],
  presets: [
    [
      "@babel/preset-env",
      {
        bugfixes: true,
        targets: {
          node: "14",
        },
      },
    ],
    "@babel/preset-typescript",
  ],
};
