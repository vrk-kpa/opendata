describe('SPARQL tests', () => {
    before(() => {
        cy.reset_db();

        // Admin things
        cy.login_post_request('admin', 'administrator');

        cy.logout_request();

        // User things
        cy.create_organization_for_user('testi_organisaatio', 'test-user');
        cy.login_post_request('test-user', 'test-user');

        // Create datasets
        const datasets = [
            {
                name: 'first dataset',
                data: {
                    "#field-title_translated-fi": 'first dataset',
                    '#field-notes_translated-fi': 'First dataset description',
                    // FIXME: This should just be 'test_keyword{enter}', see fill_form_fields in support/commands.js
                    '#s2id_autogen1': {type: 'select2', values: ['test_keyword']},
                    '#field-maintainer': 'test maintainer',
                    '#field-maintainer_email': 'test.maintainer@example.com',
                    '#field-valid_from': '2019-02-04',
                    '#field-valid_till': '2020-02-04',
                    '#field-license_id': {
                        type: 'select',
                        value: 'cc-by-4.0'
                    }
                },
                resource_data: {
                    '#field-name_translated-fi': 'test data',
                    '#field-description_translated-fi': 'test kuvaus',
                    '#field-image-url': 'http://example.com',
                    '#field-format': {
                        value: 'CSV',
                        force: true
                    },
                }
            },
            {
                name: 'second dataset',
                data: {
                    "#field-title_translated-fi": 'second dataset',
                    '#field-notes_translated-fi': 'second dataset description with unicorns',
                    // FIXME: This should just be 'another_keyword {enter} test_keyword {enter}',
                    // see fill_form_fields in support/commands.js
                    '#s2id_autogen1': {type: 'select2', values: ['another_keyword', 'test_keyword'] },
                    '#field-maintainer': 'test maintainer',
                    '#field-maintainer_email': 'test.maintainer@example.com',
                    '#field-valid_from': '2019-02-04',
                    '#field-valid_till': '2020-02-04'
                },
                resource_data: {
                    '#field-name_translated-fi': 'some test data',
                    '#field-description_translated-fi': 'description for data',
                    '#field-image-url': 'http://example.com',
                    '#field-format': {
                        value: 'XML',
                        force: true
                    },
                }
            },
        ];
        for (let dataset of datasets) {
            cy.create_new_dataset(dataset.name, dataset.data, dataset.resource_data);
        }

        // Navigate to SPARQL query view
        cy.visit('/data/sparql')
    });

    it('SPARQL dataset title query', function(){
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
