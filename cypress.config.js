const { defineConfig } = require('cypress')

module.exports = defineConfig({
  projectId: 'ssb2ut',
  env: {
    resetDB: true,
    cloudStorageEnabled: false,
    docker: true
  },
  e2e: {
    // We've imported your old cypress plugins here.
    // You may want to clean this up later by importing these.
    setupNodeEvents(on, config) {
      return require('./cypress/plugins/index.js')(on, config)
    },
    baseUrl: 'http://localhost',
    specPattern: 'cypress/e2e/**/*.{js,jsx,ts,tsx}',
  },
})
