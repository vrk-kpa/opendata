describe('SPARQL tests', () => {
    before(() => {
        cy.reset_db();

        // User things
        cy.ensure_user_is_in_ckan("admin", "administrator")
        cy.ensure_user_is_in_ckan("test-user", "test-user")
        cy.perform_ckan_actions(ckan => {
          const test_organization = 'testi_organisaatio'
          ckan.organization(test_organization, {
            users: [{
              name: 'test-user',
              capacity: "admin"
            }]
          })
          ckan.dataset(test_organization, "first_dataset", {
            "title_translated-fi": "first dataset",
            "notes_translated-fi": "First dataset description",
            "maintainer": "test maintainer",
            "maintainer_email": "test.maintainer@example.com",
            'valid_from': '2019-02-04',
            'valid_till': '2020-02-04',
            "collection_type": "Open Data",
            "keywords-fi": "test_keyword",
            "license_id": "cc-by-4.0",
          })
          ckan.resource("first_dataset", {
            "name_translated-fi": "test data",
            "description_translated-fi": "test kuvaus",
            "url": "http://example.com",
            "format": "CSV"
          })

          ckan.dataset(test_organization, "second_dataset", {
            "title_translated-fi": "second dataset",
            "notes_translated-fi": "second dataset description with unicorns",
            "maintainer": "test maintainer",
            "maintainer_email": "test.maintainer@example.com",
            'valid_from': '2019-02-04',
            'valid_till': '2020-02-04',
            "collection_type": "Open Data",
            "keywords-fi": "another_keyword test_keyword",
            "license_id": "notspecified"
          })
          ckan.resource("second_dataset", {
            "name_translated-fi": "some test data",
            "description_translated-fi": "description for data",
            "url": "http://example.com",
            "format": "XML"
          })
        })

        // Wait for fuseki to index the datasets
        cy.wait(5000)
    });

    // The change sometimes takes a while to propagate to fuseki, so try three times 
    it('SPARQL dataset title query', { retries: 3 }, function(){
        // Navigate to SPARQL query view
        cy.visit('/data/sparql')

        const query = 'PREFIX dcat: <http://www.w3.org/ns/dcat#> PREFIX dct: <http://purl.org/dc/terms/> SELECT ?s ?title WHERE { ?s dct:title ?title; a dcat:Dataset . } LIMIT 10'

        // CodeMirror requires special clearing
        cy.get('.CodeMirror')
          .first()
          .then((editor) => { editor[0].CodeMirror.setValue('') })

        cy.get('.yasqe textarea')
          .type(query, {parseSpecialCharSequences: false})
          .should('have.value', query)

        cy.get('.yasqe_queryButton').click()
        cy.get('.yasr_results').contains('first dataset')
        cy.get('.yasr_results').contains('second dataset')
    });

});
