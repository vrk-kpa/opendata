require('cypress-plugin-retries');
module.exports = (on, config) => {
  require('cypress-plugin-retries/lib/plugin')(on)
};
