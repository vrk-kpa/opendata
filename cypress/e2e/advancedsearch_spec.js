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

    describe('Navigation', () =>{
        it("Navigating to advanced search from the front page", function(){
            cy.visit('/');
            // open dataset page manually and wait page to load
            cy.get('.opendata-menu-container > .nav > :nth-child(2) > a').click();
            cy.location('pathname').should('contain', `data/fi/dataset`)
            //open advanced search page manually and wait for load
            cy.get('.mb-2 > .btn-avoindata-header').click();
            cy.location('pathname').should('contain', `data/fi/advanced_search`)
        })

    })

    describe('Translations', () => {   

        it("Advanced search sidebar contains elements FI", function() {
            cy.switch_language('fi');
            cy.get('#advanced-search-options');
            cy.get('#search-options-header').find('h3.advanced-search__title').contains('Rajaa hakua');
            cy.get('[data-module-name="dataset_type"]').find('label[for="advanced-search-dropdown-toggle-dataset_type"]').contains('Haun kohdistuminen');
            cy.get('[data-module-name="dataset_type"]').find('button[for="advanced-search-dropdown-toggle-dataset_type"]');
    
            cy.get('[data-module-name="publisher"]').find('label[for="advanced-search-dropdown-toggle-publisher"]').contains('Tuottaja');
            cy.get('[data-module-name="publisher"]').find('button[for="advanced-search-dropdown-toggle-publisher"]');
    
            cy.get('[data-module-name="category"]').find('label[for="advanced-search-dropdown-toggle-category"]').contains('Kategoria');
            cy.get('[data-module-name="category"]').find('button[for="advanced-search-dropdown-toggle-category"]');
    
            cy.get('label#release-interval-label').contains('Julkaistu välillä');
            cy.get('.released-picker-div').find('label').eq(0).contains('alkaen');
            cy.get('.released-picker-div').find('label').eq(1).contains('päättyen');
            cy.get('.released-picker-div').find('.ytp-input-with-icon').eq(0);
            cy.get('.released-picker-div').find('.ytp-input-with-icon').eq(1);
    
            cy.get('label#update-interval-label').contains('Päivitetty välillä');
            cy.get('.updated-picker-div').find('label').eq(0).contains('alkaen');
            cy.get('.updated-picker-div').find('label').eq(1).contains('päättyen');
            cy.get('.updated-picker-div').find('.ytp-input-with-icon').eq(0);
            cy.get('.updated-picker-div').find('.ytp-input-with-icon').eq(1);
    
            cy.get('[data-target="#search-options-extras"]').find('span').contains('Näytä vähemmän hakuehtoja');
    
            cy.get('[data-module-name="license"]').find('label[for="advanced-search-dropdown-toggle-license"]').contains('Lisenssi');
            cy.get('[data-module-name="license"]').find('button[for="advanced-search-dropdown-toggle-license"]');
    
            cy.get('[data-module-name="format"]').find('label[for="advanced-search-dropdown-toggle-format"]').contains('Muoto');
            cy.get('[data-module-name="format"]').find('button[for="advanced-search-dropdown-toggle-format"]');
        });
    
        it("Advanced search sidebar contains elements EN", function() {
            cy.switch_language('en');
            cy.get('#advanced-search-options');
            cy.get('#search-options-header').find('h3.advanced-search__title').contains('Filter search');
            cy.get('[data-module-name="dataset_type"]').find('label[for="advanced-search-dropdown-toggle-dataset_type"]').contains('Search target');
            cy.get('[data-module-name="dataset_type"]').find('button[for="advanced-search-dropdown-toggle-dataset_type"]');
    
            cy.get('[data-module-name="publisher"]').find('label[for="advanced-search-dropdown-toggle-publisher"]').contains('Publisher');
            cy.get('[data-module-name="publisher"]').find('button[for="advanced-search-dropdown-toggle-publisher"]');
    
            cy.get('[data-module-name="category"]').find('label[for="advanced-search-dropdown-toggle-category"]').contains('Category');
            cy.get('[data-module-name="category"]').find('button[for="advanced-search-dropdown-toggle-category"]');
    
            cy.get('label#release-interval-label').contains('Published between');
            cy.get('.released-picker-div').find('label').eq(0).contains('after');
            cy.get('.released-picker-div').find('label').eq(1).contains('before');
            cy.get('.released-picker-div').find('.ytp-input-with-icon').eq(0);
            cy.get('.released-picker-div').find('.ytp-input-with-icon').eq(1);
    
            cy.get('label#update-interval-label').contains('Updated between');
            cy.get('.updated-picker-div').find('label').eq(0).contains('after');
            cy.get('.updated-picker-div').find('label').eq(1).contains('before');
            cy.get('.updated-picker-div').find('.ytp-input-with-icon').eq(0);
            cy.get('.updated-picker-div').find('.ytp-input-with-icon').eq(1);
    
            cy.get('[data-target="#search-options-extras"]').find('span').contains('Show less options');
    
            cy.get('[data-module-name="license"]').find('label[for="advanced-search-dropdown-toggle-license"]').contains('License');
            cy.get('[data-module-name="license"]').find('button[for="advanced-search-dropdown-toggle-license"]');
    
            cy.get('[data-module-name="format"]').find('label[for="advanced-search-dropdown-toggle-format"]').contains('Format');
            cy.get('[data-module-name="format"]').find('button[for="advanced-search-dropdown-toggle-format"]');
        });
    
        it("Advanced search sidebar contains elements SV", function() {
            cy.switch_language('sv');
            cy.get('#advanced-search-options');
            cy.get('#search-options-header').find('h3.advanced-search__title').contains('Filtrera sökning');
            cy.get('[data-module-name="dataset_type"]').find('label[for="advanced-search-dropdown-toggle-dataset_type"]').contains('Sökobjekt');
            cy.get('[data-module-name="dataset_type"]').find('button[for="advanced-search-dropdown-toggle-dataset_type"]');
    
            cy.get('[data-module-name="publisher"]').find('label[for="advanced-search-dropdown-toggle-publisher"]').contains('Producent');
            cy.get('[data-module-name="publisher"]').find('button[for="advanced-search-dropdown-toggle-publisher"]');
    
            cy.get('[data-module-name="category"]').find('label[for="advanced-search-dropdown-toggle-category"]').contains('Kategori');
            cy.get('[data-module-name="category"]').find('button[for="advanced-search-dropdown-toggle-category"]');
    
            cy.get('label#release-interval-label').contains('Publicerad mellan');
            cy.get('.released-picker-div').find('label').eq(0).contains('från');
            cy.get('.released-picker-div').find('label').eq(1).contains('till');
            cy.get('.released-picker-div').find('.ytp-input-with-icon').eq(0);
            cy.get('.released-picker-div').find('.ytp-input-with-icon').eq(1);
    
            cy.get('label#update-interval-label').contains('Uppdaterad mellan');
            cy.get('.updated-picker-div').find('label').eq(0).contains('från');
            cy.get('.updated-picker-div').find('label').eq(1).contains('till');
            cy.get('.updated-picker-div').find('.ytp-input-with-icon').eq(0);
            cy.get('.updated-picker-div').find('.ytp-input-with-icon').eq(1);
    
            cy.get('[data-target="#search-options-extras"]').find('span').contains('Visa färre sökvillkor');
    
            cy.get('[data-module-name="license"]').find('label[for="advanced-search-dropdown-toggle-license"]').contains('Licens');
            cy.get('[data-module-name="license"]').find('button[for="advanced-search-dropdown-toggle-license"]');
    
            cy.get('[data-module-name="format"]').find('label[for="advanced-search-dropdown-toggle-format"]').contains('Format');
            cy.get('[data-module-name="format"]').find('button[for="advanced-search-dropdown-toggle-format"]');
        });
    });

    describe('Search tests', () => {    
        it('Searching with parameter that matches one dataset', () => {
            cy.get('.dataset-list').children().should('have.length', 2);
            fill_and_submit({
                '#advanced-search-keywords': 'first'
            });
            cy.get('.dataset-list').children().should('have.length', 1);
            cy.get('.dataset-heading').contains('first dataset');
        });
    
        it('Search with parameter that both have in common', () => {
            cy.get('.dataset-list').children().should('have.length', 2);
            fill_and_submit({
                '#advanced-search-keywords': 'dataset'
            })
            cy.get('.dataset-list').children().should('have.length', 2)
        });
    
        it('Search with keyword', () => {
            cy.get('.dataset-list').children().should('have.length', 2);
            fill_and_submit({
                '#advanced-search-keywords': 'another'
            })
            cy.get('.dataset-list').children().should('have.length', 1)
            cy.get('.dataset-heading').contains('second dataset')
        });
        // TODO: Test searching with multiple field
    });

    
    describe('Filter tests', () => {
        beforeEach(() => {
            // This wait time might be unnecessary, but filter tests will randomly fail without waiting between them.
            cy.wait(3000)
        })
      
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
      
        it('Filter by category', () => {
            fill_and_submit({
                'input[data-option-label="siisti kategoria"]': { type: 'check', force: true }
            })
            cy.get('.dataset-list').children().should('have.length', 1)
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

        it('Filter by published', () =>{
            //currently the test dataset will be created on the day the tests are run

            cy.intercept('**/data/*/advanced_search').as('searchReload')
            var waitTimeAfterReload = 500;

            cy.get('[name="released-after"]')
                .type('{selectAll}2000-01-01', {force: true})
                .blur()
                .wait('@searchReload')
                // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
                .wait(waitTimeAfterReload);
            cy.get('[name="released-before"]')
                .type('{selectAll}2100-01-01', {force: true})
                .blur()
                .wait('@searchReload')
                // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
                .wait(waitTimeAfterReload);

            cy.get('.dataset-list').children().should('have.length', 2)
            cy.get('.dataset-heading').contains('first dataset');
            cy.get('.dataset-heading').contains('second dataset');

            // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
            cy.get('[name="released-after"]').clear().wait('@searchReload').wait(waitTimeAfterReload);
            // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
            cy.get('[name="released-before"]').clear().wait('@searchReload').wait(waitTimeAfterReload);

            //should not return any datasets (reverse)
            cy.get('[name="released-after"]')
                .type('{selectAll}2100-01-01', {force: true})
                .blur()
                .wait('@searchReload')
                // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
                .wait(waitTimeAfterReload);
            cy.get('[name="released-before"]')
                .type('{selectAll}2000-01-01', {force: true})
                .blur()
                .wait('@searchReload')
                // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
                .wait(waitTimeAfterReload);

            cy.get('.dataset-list').should('not.exist');
        })

        it('Filter by updated', () =>{
            //currently the test dataset will be created on the day the tests are run
            cy.intercept('**/data/*/advanced_search').as('searchReload')
            var waitTimeAfterReload = 500;

            // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
            cy.get('[name="updated-after"]')
                .type('{selectAll}2000-01-01', {force: true})
                .blur()
                .wait('@searchReload')
                // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
                .wait(waitTimeAfterReload);
            cy.get('[name="updated-before"]')
                .type('{selectAll}2100-01-01', {force: true})
                .blur()
                .wait('@searchReload')
                // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
                .wait(waitTimeAfterReload);

            cy.get('.dataset-list').children().should('have.length', 2)
            cy.get('.dataset-heading').contains('first dataset');
            cy.get('.dataset-heading').contains('second dataset');

            // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
            cy.get('[name="updated-after"]').clear().wait('@searchReload').wait(waitTimeAfterReload);
            // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
            cy.get('[name="updated-before"]').clear().wait('@searchReload').wait(waitTimeAfterReload);

            //should not return any datasets (reverse)
            cy.get('[name="updated-after"]')
                .type('{selectAll}2100-01-01', {force: true})
                .blur()
                .wait('@searchReload')
                // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
                .wait(waitTimeAfterReload);
            cy.get('[name="updated-before"]')
                .type('{selectAll}2000-01-01', {force: true})
                .blur()
                .wait('@searchReload')
                // @NOTE: Additional wait time is needed after page refresh so that javascript has time to initialize
                .wait(waitTimeAfterReload);

            cy.get('.dataset-list').should('not.exist');
        })

        // TODO: Test publisher filter
        // TODO: Test querying all from a multiselect
    })


    // TODO: Test pagination (with search queries and without)

    describe('Sorting tests', function(){

        it('Advanced search has sorting options', function(){
        cy.get('#field-order-by > option').eq(0).should('have.value', 'score desc, metadata_created desc');
        cy.get('#field-order-by > option').eq(1).should('have.value', 'title_string asc');
        cy.get('#field-order-by > option').eq(2).should('have.value', 'title_string desc');
        cy.get('#field-order-by > option').eq(3).should('have.value', 'metadata_modified desc');
        cy.get('#field-order-by > option').eq(4).should('have.value', 'metadata_created asc');
        cy.get('#field-order-by > option').eq(5).should('have.value', 'metadata_created desc');
        cy.get('#field-order-by > option').eq(6).should('have.value', 'views_recent desc');
        });

        it('Default sorting option is sorting by relevance', function(){
        cy.get('#field-order-by').should('have.value', 'score desc, metadata_created desc');
        cy.location('pathname').should('contain', `data/fi/advanced_search`)
        });
    
    });

});

