describe('Advanced search tests', () => {
    before(() => {
        cy.reset_db();

        // Admin things
        cy.login_post_request('admin', 'administrator');

        const category_name_1 = 'siisti kategoria';
        const category_name_2 = 'toinen kategoria';

        cy.create_category(category_name_1);
        cy.create_category(category_name_2);

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
                        value: 'cc-by'
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

        // Add first dataset to group 'siisti kategoria'
        cy.visit(`/data/fi/dataset/groups/${datasets[0].name.replace(' ', '-')}`)
        cy.get('#field-siisti-kategoria').check({force: true})
        cy.get('button[type=submit]').click()

        // Navigate to advanced search
        cy.visit('/data/fi/advanced_search')
    });

    beforeEach(() => {
        // Use visit to clear search fields
        // the timeout after visiting the url should be enough to let all the javascript load
        cy.visit('/data/fi/advanced_search')
    })

    const fill_and_submit = (data) => {
        cy.fill_form_fields(data)
        cy.get('button[type=submit]').click();
    }

  /*
    describe('Test that advanced search loads correctly', () => {
        it('Check that initial results are shown', () => {
            cy.get('.dataset-list').children().should('have.length', 2)
        })
    })

    describe('Test querying by string and target', () => {
        it('Searching with query "first"', () => {
            fill_and_submit({
                '#advanced-search-keywords': 'first'
            })
            cy.get('.dataset-list').children().should('have.length', 1)
            cy.get('.dataset-heading').contains('first dataset')
        });

        it('Searching with query "second"', () => {
            fill_and_submit({
                '#advanced-search-keywords': 'second'
            })
            cy.get('.dataset-list').children().should('have.length', 1)
        });

        it('Search with what both have in common', () => {
            fill_and_submit({
                '#advanced-search-keywords': 'dataset'
            })
            cy.get('.dataset-list').children().should('have.length', 2)
        })

        it('Search with keyword', () => {
            fill_and_submit({
                '#advanced-search-keywords': 'another'
            })
            cy.get('.dataset-list').children().should('have.length', 1)
            cy.get('.dataset-heading').contains('second dataset')
        })
    })
*/
    describe('Use multiple select to filter query', () => {
        beforeEach(() => {
            cy.wait(3000)
        })
      /*
        it('Open multiple select', () => {
            cy.get('#category-choicelist').should('not.be.visible')
            cy.get('button[for=advanced-search-dropdown-toggle-category]').click();
            cy.get('#category-choicelist').should('be.visible')
        })

        it('Select all by clicking "All" -option', () => {
            cy.get('button[for=advanced-search-dropdown-toggle-format]').click();
            cy.get('#format-checkbox-all').check({ force: true })
            cy.get('#format-checkbox-csv').should('be.checked')
            cy.get('button[for=advanced-search-dropdown-toggle-format]').contains('Kaikki')
        })

        it('Selects all by clicking all other options and not "all" -button', () => {
            cy.get('#format-checkbox-all').should('not.be.checked')
            cy.get('#format-checkbox-csv').check({ force: true })
            cy.get('#format-checkbox-xml').check({ force: true })
            cy.get('button[for=advanced-search-dropdown-toggle-format]').contains('Kaikki')
            cy.get('#format-checkbox-all').should('be.checked')
        })
      */
        it('Filter by category', () => {
            fill_and_submit({
                'input[data-option-label="siisti kategoria"]': { type: 'check', force: true }
            })
            cy.get('.dataset-list', {timeout: 30000}).children().should('have.length', 1)
            cy.get('.dataset-heading').contains('first dataset')
        })
        it('Filter by license', () => {
            fill_and_submit({
                '#license-checkbox-notspecified': { type: 'check', force: true }
            })
            cy.get('.dataset-list').children().should('have.length', 1)
            cy.get('.dataset-heading').contains('second dataset')
        })
        it('Filter by resource format', () => {
            fill_and_submit({
                '#format-checkbox-csv': { type: 'check', force: true }
            })
            cy.get('.dataset-list').children().should('have.length', 1)
            cy.get('.dataset-heading').contains('first dataset')
        })
        // TODO: Test publisher filter
        // TODO: Test querying all from a multiselect
    })

    // TODO: Test filtering by release date
    // TODO: Test filtering by updated date
    // TODO: Test searching with multiple field
    // TODO: Test pagination (with search queries and without)
});
