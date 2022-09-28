describe('Dataset resource tests', function(){
    const dataset_name = 'test_dataset';

    before(function(){
        cy.reset_db();
        cy.create_organization_for_user('dataset_test_organization', 'test-user', true);
        cy.login_post_request('test-user', 'test-user')
        cy.visit('/data/fi/dataset');
        const dataset_name = 'test_dataset';
        cy.create_new_dataset(dataset_name); 
    })

    beforeEach(function () {
        cy.login_post_request('test-user', 'test-user')
        cy.visit('/');
        cy.get('nav a[href="/data/fi/dataset"]').click();
        // const dataset_name = 'test_dataset';
        cy.get(`a[href="/data/fi/dataset/${dataset_name}"]`).click();
        cy.get('.resource-item__info__title').click();
      })

    it("Can't edit resource while not logged in", function() {
        cy.logout_request();
        cy.visit('/');
        cy.get('nav a[href="/data/fi/dataset"]').click();
        cy.get(`a[href="/data/fi/dataset/${dataset_name}"]`).click();
        cy.get('.resource-item__info__title').click();
    
        cy.get('.actions').find('a').contains('Muokkaa').should('not.exist');
    });

    it('Test dataset resource links', function(){
        cy.switch_language('fi');
        //This will fail if db isn't reset before running this test
        cy.get('.prose').find('p').find('a').click();
        cy.location('pathname').should('contain', `/data/fi/dataset/${dataset_name}`);
        cy.go('back');

        cy.get('.data-viewer-info').find('a').click();
        cy.get('.nav--resource-list').find('.active').click();

        //breadcrumbs
        cy.get('.breadcrumb').find('li').eq(0).click();
        cy.location('pathname').should('not.contain', `/data/`);
        cy.go('back');
        
        cy.get('.breadcrumb').find('li').eq(1).click();
        cy.location('pathname').should('contain', `/data/fi/organization/`);
        cy.go('back');

        cy.get('.breadcrumb').find('li').eq(2).click();
        cy.location('pathname').should('contain', `/data/fi/organization/dataset_test_organization`);
        cy.go('back');

        cy.get('.breadcrumb').find('li').eq(3).click();
        cy.location('pathname').should('contain', `/data/fi/dataset/${dataset_name}`);
        cy.go('back');

        cy.get('.breadcrumb').find('li').eq(4).click();
        // page should stay the same
        
        cy.get('.actions').find('a').contains('Muokkaa').click();
        cy.location('pathname').should('contain', `/edit`);
        cy.go('back');
        //some datasets link to a webpage instead of having a download link
        //This gets cors blocked because it tries to open example.com, so don't click
        cy.get('.actions').find('.resource-url-analytics').should('have.attr', 'href').should('eq', 'http://example.com');
    
        cy.get('.toolbar-resource-secondary').find('a').click();
        cy.location('pathname').should('contain', `/data/fi/dataset/${dataset_name}`);
        cy.go('back');
    });

    describe('Test Translations', function(){
        //Note! This edits a separate dataset so other tests won't be affected
        it('Test edit dataset name languages', function(){

            cy.visit('/');
            cy.get('nav a[href="/data/fi/dataset"]').click();
            const dataset_name = 'test_edit_dataset';
            cy.create_new_dataset(dataset_name); 
            cy.get(`a[href="/data/fi/dataset/${dataset_name}"]`).click();
            cy.get('.resource-item__info__title').click();

            cy.switch_language('fi');
            cy.get('.actions').find('a').contains('Muokkaa').click();

            const finnish_dataset_name = "testi datasetti";
            const english_dataset_name = "test dataset";
            const swedish_dataset_name = "test datamängd";
            const finnish_dataset_description = "tämä on suomalainen kuvaus";
            const english_dataset_description = "this is the english description";
            const swedish_dataset_description = "detta är den svenksa beskrivningen";

            //update the fields
            cy.get('#field-name_translated-fi').clear().type(finnish_dataset_name);
            cy.get('#field-name_translated-en').clear().type(english_dataset_name);
            cy.get('#field-name_translated-sv').clear().type(swedish_dataset_name);
            cy.get('#field-description_translated-fi').clear().type(finnish_dataset_description);
            cy.get('#field-description_translated-en').clear().type(english_dataset_description);
            cy.get('#field-description_translated-sv').clear().type(swedish_dataset_description);

            cy.get('[name="save"]').click();

            //check that the dataset name was updated in all languages
            cy.get('.page-heading').contains(finnish_dataset_name);
            cy.get('.prose').find('p').contains(finnish_dataset_description)
            cy.switch_language('en');
            cy.get('.page-heading').contains(english_dataset_name);
            cy.get('.prose').find('p').contains(english_dataset_description)
            cy.switch_language('sv');
            cy.get('.page-heading').contains(swedish_dataset_name);
            cy.get('.prose').find('p').contains(swedish_dataset_description)

        });

        it('Finnish UI elements', function() {
            cy.switch_language('fi');
            const dataset_name = "test_dataset";
            const dataset_data = "test data";
            
            //breadcrumbs
            cy.get('.breadcrumb').find('li').eq(0).contains('Etusivu');
            cy.get('.breadcrumb').find('li').eq(1).contains('Tuottajat');
            cy.get('.breadcrumb').find('li').eq(2);//this has autogenerated uid in it
            cy.get('.breadcrumb').find('li').eq(3).contains(dataset_name);
            cy.get('.breadcrumb').find('li').eq(4).contains(dataset_data);
        
            //sidebar
            cy.get('.secondary').find('h2').contains('Data-aineistot');
            cy.get('.secondary').find('li').find('a').contains('test data');
        
            //dataset titles, actions and heading
            cy.get('.module-small-title').contains(dataset_name);
            cy.get('.actions').find('a').contains('Muokkaa');
            cy.get('.actions').find('a').contains('Avaa');
            cy.get('.page-heading').contains(dataset_data);
        
            //dataset summary
            cy.get('.prose').find('h3').contains("Tietoaineiston yhteenvedosta");
            cy.get('.prose').find('blockquote').find('p').contains("Dataset test description");
            cy.get('.prose').find('p').contains('Lähde:');
            cy.get('.prose').find(`a[href="/data/fi/dataset/${dataset_name}"]`);
        
            //dataset preview
            cy.get('.resource-view').find('h3').contains("Esikatselu");
            cy.get('.data-viewer-info').find('p').contains("Data-aineistolle ei ole lisätty esikatselunäkymiä.");
            //requires user to be logged in and viewing their own dataset
            cy.get('.data-viewer-info').find('p').contains("Puuttuvatko odottamasi esikatselunäkymät?");
            cy.get('.data-viewer-info').find('p').find('a').contains('Klikkaa tästä saadaksesi lisätietoa.');
        
            //dataset info table
            cy.get('.module-content').find('h3').contains("Lisätietoja"); //there isn't a good identifier to find this element without using the contains text
            cy.get('.resource-module-table');
            cy.get('.resource-module-table').find('th').contains("Muoto");
            cy.get('.resource-module-table').find('th').contains("Aineiston tila");
            cy.get('.resource-module-table').find('th').contains("Sijaintikoordinaattien muoto");
            cy.get('.resource-module-table').find('th').contains("Katettu ajanjakso");
            cy.get('.resource-module-table').find('th').contains("Viimeisin päivitys");
            cy.get('.resource-module-table').find('th').contains("Luotu");
            cy.get('.resource-module-table').find('th').contains("SHA256");
        });
        
        it('English UI elements', function() {
            const dataset_name = "test_dataset";
            const dataset_data = "test data";
            cy.switch_language('en');
            //breadcrumbs
            cy.get('.breadcrumb').find('li').eq(0).contains('Home');
            cy.get('.breadcrumb').find('li').eq(1).contains('Publishers');
            cy.get('.breadcrumb').find('li').eq(2);//this has autogenerated uid in it
            cy.get('.breadcrumb').find('li').eq(3).contains(dataset_name);
            cy.get('.breadcrumb').find('li').eq(4).contains(dataset_data);
        
            //sidebar
            cy.get('.secondary').find('h2').contains('Resources');
            cy.get('.secondary').find('li').find('a').contains('test data');
        
            //dataset titles, actions and heading
            cy.get('.module-small-title').contains(dataset_name);
            cy.get('.actions').find('a').contains('Manage');
            cy.get('.actions').find('a').contains('Open');
            cy.get('.page-heading').contains(dataset_data);
        
            //dataset summary
            cy.get('.prose').find('h3').contains("From the dataset abstract");
            cy.get('.prose').find('blockquote').find('p').contains("Dataset test description");
            cy.get('.prose').find('p').contains('Source:');
            cy.get('.prose').find(`a[href="/data/en_GB/dataset/${dataset_name}"]`);
        
        
            //dataset preview
            cy.get('.resource-view').find('h3').contains("Preview");
            cy.get('.data-viewer-info').find('p').contains("There are no views created for this resource yet.");
            //requires user to be logged in and viewing their own dataset
            cy.get('.data-viewer-info').find('p').contains("Not seeing the views you were expecting?");
            cy.get('.data-viewer-info').find('p').find('a').contains('Click here for more information.');
        
            //dataset info table
            cy.get('.module-content').find('h3').contains("Extra information"); //there isn't a good identifier to find this element without using the contains text
            cy.get('.resource-module-table');
            cy.get('.resource-module-table').find('th').contains("Format");
            cy.get('.resource-module-table').find('th').contains("Data status");
            cy.get('.resource-module-table').find('th').contains("Coordinate system");
            cy.get('.resource-module-table').find('th').contains("Temporal Coverage");
            cy.get('.resource-module-table').find('th').contains("Last updated");
            cy.get('.resource-module-table').find('th').contains("Created");
            cy.get('.resource-module-table').find('th').contains("SHA256");
        });
        
        it('Swedish UI elements', function() {
            const dataset_name = "test_dataset";
            const dataset_data = "test data";
            cy.switch_language('sv');
            //breadcrumbs
            cy.get('.breadcrumb').find('li').eq(0).contains('Startsida');
            cy.get('.breadcrumb').find('li').eq(1).contains('Producenter');
            cy.get('.breadcrumb').find('li').eq(2);//this has autogenerated uid in it
            cy.get('.breadcrumb').find('li').eq(3).contains(dataset_name);
            cy.get('.breadcrumb').find('li').eq(4).contains(dataset_data);
        
            //sidebar
            cy.get('.secondary').find('h2').contains('Dataresurser');
            cy.get('.secondary').find('li').find('a').contains('test data');
        
            //dataset titles, actions and heading
            cy.get('.module-small-title').contains(dataset_name);
            cy.get('.actions').find('a').contains('Redigera');
            cy.get('.actions').find('a').contains('Öppna');
            cy.get('.page-heading').contains(dataset_data);
        
            //dataset summary
            cy.get('.prose').find('h3').contains("Av datasmängdens sammandrag");
            cy.get('.prose').find('blockquote').find('p').contains("Dataset test description");
            cy.get('.prose').find('p').contains('Källa:');
            cy.get('.prose').find(`a[href="/data/sv/dataset/${dataset_name}"]`);
        
        
            //dataset preview
            cy.get('.resource-view').find('h3').contains("Förhandsgranskning");
            cy.get('.data-viewer-info').find('p').contains("Inga förhandsgranskningar har skapats för denna dataresurs.");
            //requires user to be logged in and viewing their own dataset
            cy.get('.data-viewer-info').find('p').contains("Ser du inte de vyer du förväntat dig?");
            cy.get('.data-viewer-info').find('p').find('a').contains('Klicka här för mer information');
        
            //dataset info table
            cy.get('.module-content').find('h3').contains("Ytterligare information"); //there isn't a good identifier to find this element without using the contains text
            cy.get('.resource-module-table');
            cy.get('.resource-module-table').find('th').contains("Format");
            cy.get('.resource-module-table').find('th').contains("Datastatus");
            cy.get('.resource-module-table').find('th').contains("Koordinatsystem");
            cy.get('.resource-module-table').find('th').contains("Tidsmässig täckning");
            cy.get('.resource-module-table').find('th').contains("Senaste uppdatering");
            cy.get('.resource-module-table').find('th').contains("Skapad");
            cy.get('.resource-module-table').find('th').contains("SHA256");
        });
          


    });

});