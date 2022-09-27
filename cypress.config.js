const { defineConfig } = require('cypress')

const del = require('del')

module.exports = defineConfig({
  projectId: 'ssb2ut',
  env: {
    resetDB: true,
    cloudStorageEnabled: false,
    docker: true
  },
  videoCompression: 20,
  videoUploadOnPasses: false,
  defaultCommandTimeout: 30000,
  e2e: {
    baseUrl: 'http://localhost',
    specPattern: 'cypress/e2e/**/*.{js,jsx,ts,tsx}',
    //https://docs.cypress.io/api/plugins/after-spec-api#Log-the-relative-spec-path-to-stdout-after-the-spec-is-run
    // need to install the "del" module as a dependency
    setupNodeEvents(on, config) {
      on('after:spec', (spec, results) => {
        if (results && results.stats.failures === 0 && results.video) {
          // `del()` returns a promise, so it's important to return it to ensure
          // deleting the video is finished before moving on
          return del(results.video)
        }
      })
    },

  },

  

})
