const { defineConfig } = require('cypress')

module.exports = defineConfig({
  projectId: 'ssb2ut',
  env: {
    resetDB: true,
    cloudStorageEnabled: false,
    docker: true
  },
  e2e: {
    baseUrl: 'http://localhost',
    specPattern: 'cypress/e2e/**/*.{js,jsx,ts,tsx}',
  },
})
