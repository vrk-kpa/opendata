describe('Advanced search tests', () => {
    before(() => {
        cy.reset_db();
        cy.perform_ckan_actions(ckan => {
          ckan.group("siisti_kategoria", {
            "title_translated-fi": "siisti kategoria",
            "title_translated-en": "siisti kategoria",
            "title_translated-sv": "siisti kategoria",
            "users": [
              {"name": "admin",
               "capacity": "admin"},
              {"name": "test-user",
               "capacity": "admin"}
            ]
          }, {failOnStatusCode: false}) // Admin making groups creates an unnecessary error
          ckan.group("toinen_kategoria", {
            "title_translated-fi": "toinen kategoria",
            "title_translated-en": "toinen kategoria",
            "title_translated-sv": "toinen kategoria",
            "users": [
              {"name": "admin",
               "capacity": "admin"},
              {"name": "test-user",
               "capacity": "admin"}
            ]
          }, {failOnStatusCode: false}) // Admin making groups creates an unnecessary error

          ckan.organization("testi_organisaatio")

          ckan.dataset("testi_organisaatio", "first_dataset", {
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
          ckan.action('member_create', {
            "id": "siisti_kategoria",
            "object": "first_dataset",
            "object_type": "package",
            "capacity": "member"
          })

          ckan.dataset("testi_organisaatio", "second_dataset", {
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

        cy.login_post_request('test-user', 'test-user');
        cy.visit('/data/fi/advanced_search')
    });

    beforeEach(() => {
        // Use visit to clear search fields
        // the timeout after visiting the url should be enough to let all the javascript load
        cy.visit('/data/fi/advanced_search')
    })

    const fill_and_submit = (data) => {
        cy.fill_form_fields(data);
        cy.get('.ytp-input-with-icon > button').click();
    }

    describe('Navigation', () =>{
        it("Navigating to advanced search from the front page", function(){
            cy.visit('/');
            // open dataset page manually and wait page to load
            cy.get('.opendata-menu-container a[href="/data/fi/dataset"]').click({
                // Disable scrolling so drupal toolbar doesn't cover the link
                scrollBehavior: false
            });
            cy.location('pathname').should('contain', `data/fi/dataset`)
            //open advanced search page manually and wait for load
            cy.get('.mb-2 > .btn-avoindata-link').click();
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

            cy.get('#date-picker-released-after');
            cy.get('#date-picker-released-before');
    
            cy.get('label#update-interval-label').contains('Päivitetty välillä');
            cy.get('.updated-picker-div').find('label').eq(0).contains('alkaen');
            cy.get('.updated-picker-div').find('label').eq(1).contains('päättyen');
            cy.get('#date-picker-updated-after');
            cy.get('#date-picker-updated-before');
    
            cy.get('[data-bs-target="#search-options-extras"]').find('span').contains('Näytä vähemmän hakuehtoja');
    
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

            cy.get('#date-picker-released-after');
            cy.get('#date-picker-released-before');
    
            cy.get('label#update-interval-label').contains('Updated between');
            cy.get('.updated-picker-div').find('label').eq(0).contains('after');
            cy.get('.updated-picker-div').find('label').eq(1).contains('before');
            cy.get('#date-picker-updated-after');
            cy.get('#date-picker-updated-before');
    
            cy.get('[data-bs-target="#search-options-extras"]').find('span').contains('Show less options');
    
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

            cy.get('#date-picker-released-after');
            cy.get('#date-picker-released-before');
    
            cy.get('label#update-interval-label').contains('Uppdaterad mellan');
            cy.get('.updated-picker-div').find('label').eq(0).contains('från');
            cy.get('.updated-picker-div').find('label').eq(1).contains('till');
            cy.get('#date-picker-updated-after');
            cy.get('#date-picker-updated-before');
    
            cy.get('[data-bs-target="#search-options-extras"]').find('span').contains('Visa färre sökvillkor');
    
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

            // Filter a daterange that should contain all datasets
            cy.get('#date-picker-released-after').type('2000-01-01');
            cy.get('#date-picker-released-before').type('2200-01-01').type('{enter}');
            cy.get('.dataset-list').children().should('have.length', 2)
            cy.get('.dataset-heading').contains('first dataset');
            cy.get('.dataset-heading').contains('second dataset');

            // Clear the inputs
            cy.get('#date-picker-released-after').type('2000-01-01').clear();
            cy.get('#date-picker-released-before').type('2000-01-01').clear();

            // Filter a daterange that should not contain any datasets
            cy.get('#date-picker-released-after').type('2200-01-01');
            cy.get('#date-picker-released-before').type('2000-01-01').type('{enter}');
            
            cy.get('.dataset-list').should('not.exist');
        })

        it('Filter by updated', () =>{
            //currently the test dataset will be created on the day the tests are run

            // Filter a daterange that should contain all datasets
            cy.get('#date-picker-updated-after').type('2000-01-01');
            cy.get('#date-picker-updated-before').type('2200-01-01').type('{enter}');
            cy.get('.dataset-list').children().should('have.length', 2)
            cy.get('.dataset-heading').contains('first dataset');
            cy.get('.dataset-heading').contains('second dataset');

            // Clear the inputs
            cy.get('#date-picker-updated-after').type('2000-01-01').clear();
            cy.get('#date-picker-updated-before').type('2000-01-01').clear();


            // Filter a daterange that should not contain any datasets
            cy.get('#date-picker-updated-after').type('2200-01-01');
            cy.get('#date-picker-updated-before').type('2000-01-01').type('{enter}');
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
        });

        it('Default sorting option is sorting by relevance', function(){
        cy.get('#field-order-by').should('have.value', 'score desc, metadata_created desc');
        cy.location('pathname').should('contain', `data/fi/advanced_search`)
        });
    
    });

});
