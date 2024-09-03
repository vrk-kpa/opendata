
describe('Dataset tests',
  {
    retries:{
      runMode: 2,
      openMode: 2,
    }
  }, function(){
  const test_organization = 'dataset_test_organization';

  before(function(){
    cy.reset_db();
    cy.create_organization_for_user(test_organization, 'test-user', true);
  });

  describe('Navigation', function(){
    it('Navigate to the dataset page', function(){
      // open dataset page manually
      cy.get('.opendata-menu-container > .nav > :nth-child(2) > a').click();
      // wait for page to load (note the path containing /fi/)
      cy.location('pathname').should('contain', `data/fi/dataset`)
    });
  });

  describe('Dataset sorting tests', function(){
    const dataset_name_1 = "first_dataset";
    const dataset_name_2 = "second_dataset";

    before(function(){
      // cy.reset_db();
      // cy.create_organization_for_user(test_organization, 'test-user', true);
      cy.login_post_request('test-user', 'test-user')
      cy.visit('/data/dataset');
      cy.create_new_dataset(dataset_name_1);
      cy.create_new_dataset(dataset_name_2);
    });

    beforeEach(function(){
      // keep the /fi/ in the url as some tests check against paths with it included
      cy.visit('/data/dataset');
    })

    it('Default sorting option is sorting by relevance', function(){
      cy.get('#field-order-by').should('have.value', 'score desc, metadata_created desc');
      cy.location('pathname', {timeout: 20000}).should('contain', `data/dataset`)
    });
    
    it('Default sorting option persists after search', function(){
      cy.visit('/data/dataset');
      cy.get('.search').type('random search');
      cy.get('.fal').click();
      cy.url({timeout: 20000}).should('contain', `dataset?q=random+search&sort=score+desc%2C+metadata_created+desc`)
      cy.get('#field-order-by').should('have.value', 'score desc, metadata_created desc');
    });

    it('Chosen sorting options changes the way datasets are sorted', function(){
      cy.get('#field-order-by').select('title_string asc');
      cy.url({timeout: 20000}).should('contain', `dataset?q=&sort=title_string+asc`)

      cy.get('#field-order-by').select('score desc, metadata_created desc');
      cy.url({timeout: 20000}).should('contain', `dataset?q=&sort=score+desc%2C+metadata_created`)

      cy.get('#field-order-by').select('title_string desc');
      cy.url({timeout: 20000}).should('contain', `dataset?q=&sort=title_string+desc`)

      cy.get('#field-order-by').select('metadata_modified desc');
      cy.url({timeout: 20000}).should('contain', `dataset?q=&sort=metadata_modified+desc`)

      cy.get('#field-order-by').select('metadata_created asc');
      cy.url({timeout: 20000}).should('contain', `dataset?q=&sort=metadata_created+asc`)

      cy.get('#field-order-by').select('metadata_created desc');
      cy.url({timeout: 20000}).should('contain', `dataset?q=&sort=metadata_created+desc`)

      cy.get('#field-order-by').select('views_recent desc');
      cy.url({timeout: 20000}).should('contain', `dataset?q=&sort=views_recent+desc`)
    });

    it('Chosen sorting option persists after search', function(){
      cy.get('#field-order-by').select('views_recent desc');
      cy.url({timeout: 20000}).should('contain', `dataset?q=&sort=views_recent+desc`)
      cy.get('.search').type('random search');
      cy.get('.fal').click();
      cy.url({timeout: 20000}).should('contain', `dataset?q=random+search&sort=views_recent+desc`)
      cy.get('#field-order-by').select('views_recent desc');
    });

    it('Datasets have sorting options', function(){
      cy.get('#field-order-by > option').eq(0).should('have.value', 'score desc, metadata_created desc');
      cy.get('#field-order-by > option').eq(1).should('have.value', 'title_string asc');
      cy.get('#field-order-by > option').eq(2).should('have.value', 'title_string desc');
      cy.get('#field-order-by > option').eq(3).should('have.value', 'metadata_modified desc');
      cy.get('#field-order-by > option').eq(4).should('have.value', 'metadata_created asc');
      cy.get('#field-order-by > option').eq(5).should('have.value', 'metadata_created desc');
      cy.get('#field-order-by > option').eq(6).should('have.value', 'views_recent desc');
    });

    // NOTE! This test currently is dependent on the ordering of the datasets, so if any datasets are created before in 
    // another describe block, the test will fail
    it('Datasets appear sorted by creation date by default', function(){  
      // check if the ordering is correct (creation date desc)
      // cy.visit('/data/dataset');
      cy.get(':nth-child(1) > .dataset-content > .align-items-center > .dataset-heading > a').should('have.text', dataset_name_2);
      cy.get(':nth-child(2) > .dataset-content > .align-items-center > .dataset-heading > a').should('have.text', dataset_name_1);

      // change the sorting to creation date asc
      cy.get('#field-order-by').select('metadata_created asc');
      cy.url({timeout: 20000}).should('include', `sort=metadata_created+asc`); //wait for page load after choosing sorting option

      cy.get(':nth-child(1) > .dataset-content > .align-items-center > .dataset-heading > a').should('have.text', dataset_name_1);
      cy.get(':nth-child(2) > .dataset-content > .align-items-center > .dataset-heading > a').should('have.text', dataset_name_2);
    });

  });

  describe('Dataset filtering tests', function(){
    it('Dataset properties are visible as filter options', function(){
      cy.visit('/data/dataset');

      cy.get(':nth-child(4) > nav > .list-unstyled > .nav-item > a > span').should('have.text', "Avoin data (2)");
      cy.get(':nth-child(5) > nav > .list-unstyled > .nav-item > a > span').should('have.text', "test_keyword (2)");
      //look for partial text as the organization can have an ID suffix 
      cy.get(':nth-child(6) > nav > .list-unstyled > .nav-item > a > span').should('include.text', "dataset_test_organization"); 
      cy.get(':nth-child(8) > nav > .list-unstyled > .nav-item > a > span').should('have.text', "Lisenssiä ei ole määritelty (2)")
    });
  });

  describe('Dataset creation and deletion tests', function() {
    beforeEach(function () {
      cy.reset_db();
      cy.create_organization_for_user(test_organization, 'test-user', true);
      cy.login_post_request('test-user', 'test-user')
      cy.visit('/data/fi/dataset');
    })

    it('Create a dataset with a category', function(){
      cy.logout_request();
      cy.login_post_request('admin', 'administrator');
      const category_name_1 = 'test_category_1';
      cy.create_category(category_name_1);
      cy.logout_request();
      cy.login_post_request('test-user', 'test-user')

      const dataset_name = 'category_test';
      const dataset_form_data = {
        "#field-title_translated-fi": dataset_name,
        '#field-notes_translated-fi': 'Dataset test description',
        // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
        '#s2id_autogen1': {type: 'select2', values: ['test_keyword']},
        '#field-maintainer': 'test maintainer',
        '#field-maintainer_email': 'test.maintainer@example.com'
      };
  
      cy.get('nav a[href="/data/fi/dataset"]').click();
      cy.get('a[href="/data/fi/dataset/new"]').click();
      cy.get('.slug-preview button').contains('Muokkaa').click();
      cy.get('#field-name').type(dataset_name);
      cy.fill_form_fields(dataset_form_data);
      cy.get('#field-groups-' + category_name_1 + ' ~ span').click();
      cy.get('button[name=save]').click();
  
      const resource_form_data = {
        "#field-name_translated-fi": 'test data',
        '#field-image-url': 'http://example.com'
      };
  
      cy.contains('a', 'Linkki').click();
      cy.fill_form_fields(resource_form_data);
      cy.get('button[name=save].suomifi-button-primary').click();

    });

    it('Create minimal dataset and add file as a resource', function(){
      const dataset_name = 'test_dataset_with_file';

      const dataset_form_data = {
        "#field-title_translated-fi": dataset_name,
        '#field-notes_translated-fi': 'Dataset test description',
        // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
        '#s2id_autogen1': {type: 'select2', values: ['test_keyword']},
        '#field-maintainer': 'test maintainer',
        '#field-maintainer_email': 'test.maintainer@example.com'
      };

      cy.get('a[href="/data/fi/dataset/new"]').click();
      cy.get('.slug-preview button').contains('Muokkaa').click();
      cy.get('#field-name').type(dataset_name);
      cy.fill_form_fields(dataset_form_data);
      cy.get('button[name=save]').click();


      const resource_name = 'sample file';
      const resource_form_data = {
        "#field-name_translated-fi": resource_name
      };

      cy.get('#field-image-upload').selectFile("cypress/FL_insurance_sample.csv")
      cy.fill_form_fields(resource_form_data);

      cy.get('button[name=save].suomifi-button-primary').click();

      // if cloudstorage is enabled, we wait for window.location to change
      if (Cypress.env('cloudStorageEnabled')){
        cy.location('pathname', {timeout: 40000}).should('not.include', '/resource/new');
      }

      cy.get('a').contains(resource_name).click();

      cy.get('a').contains('Lataa')
        .should('have.attr', 'href')
        .then(function (href) {
          cy.request(href).its('status')
            .should('eq', 200)
      });

      // File size should be calculated automatically
      // Use 'contain' because of surrounding whitespace
      cy.get('th').contains('Tiedostokoko').next()
        .should('contain.text', '4123652');
    });

    it('Create a dataset with all fields', function() {
      const dataset_name = 'test_dataset_with_all_fields';
      const dataset_form_data = {
        '#field-title_translated-fi': dataset_name,
        '#field-title_translated-en': dataset_name,
        '#field-title_translated-sv': dataset_name,
        '#field-notes_translated-fi': 'test kuvaus',
        '#field-notes_translated-en': 'test description',
        '#field-notes_translated-sv': 'test beskrivning',
        // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
        '#s2id_autogen1': {type: 'select2', values: ['test']},
        '#s2id_autogen2': {type: 'select2', values: ['test']},
        '#s2id_autogen3': {type: 'select2', values: ['test']},
        '#s2id_autogen4': {type: 'select2', values: ['test']},
        '#field-maintainer': 'test maintainer',
        '#field-maintainer_email': 'example@example.com',
        '#field-maintainer_website': 'www.example.com',
        '#field-copyright_notice_translated-fi': 'lisenssi test',
        '#field-copyright_notice_translated-en': 'lisenssi test',
        '#field-copyright_notice_translated-sv': 'lisenssi test',
        '#field-external_urls': 'http://www.example.com',
        '#field-valid_from': '2019-02-04',
        '#field-valid_till': '2020-02-04'
      };

      const resource_form_data = {
        '#field-name_translated-fi': 'test data',
        '#field-name_translated-en': 'test data',
        '#field-name_translated-sv': 'test data',
        '#field-image-url': 'http://example.com',
        '#field-description_translated-fi': 'test kuvaus',
        '#field-description_translated-en': 'test description',
        '#field-description_translated-sv': 'test beskrivning',
        '#field-position_info': '56.7 43.5',
        // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
        'label[for=field-temporal_granularity-fi] ~ div .select2-choices input': {type: 'select2', values: ['test']},
        'label[for=field-temporal_granularity-en] ~ div .select2-choices input': {type: 'select2', values: ['test']},
        'label[for=field-temporal_granularity-sv] ~ div .select2-choices input': {type: 'select2', values: ['test']},
        '#field-temporal_coverage_to': '2019-02-02',
        '#field-temporal_coverage_from': '2018-02-02'
      };
      cy.create_new_dataset(dataset_name, dataset_form_data, resource_form_data);
    });

    it('Creating an empty dataset fails', function() {
      cy.get('a[href="/data/fi/dataset/new"]').click();
      cy.get('button[name=save]').click();
      cy.get('.error-explanation');
    });

    it('Cannot create dataset if logged out', function() {
      cy.logout_request();
      cy.visit('/');
      cy.get('nav a[href="/data/fi/dataset"]').click();
      cy.get('a[href="/data/fi/dataset/new"]').should('not.exist');
    });

    it('Delete a dataset', function(){
      const deletable_dataset_name = "deletable_dataset"
      cy.create_new_dataset(deletable_dataset_name);
      cy.visit(`/data/fi/dataset/${deletable_dataset_name}`);
      cy.delete_dataset(deletable_dataset_name);
    });

  })


  describe('Dataset properties tests', function(){
    const misc_dataset_name = "misc_dataset";
    const misc_dataset_description_if = "testi kuvaus";
    const test_tag = "testing tag";
    const dataset_maintainer_email = "example@example.com";
    const dataset_maintainer_website = "www.example.com";
    const dataset_external_url = "https://www.example.com";
    const dataset_update_interval = "Päivittäin";
    const licence_text = "Creative Commons Non-Commercial";
    const valid_from = "2019-02-04";
    const valid_till = "2020-02-04";
    //dates get converted to DD.mm.YYYY format in the view
    const check_from = "04.02.2019";
    const check_till = "04.02.2020";
    //date that will be to compare when the dataset collection was created or edited
    let today = new Date();
    let dd = String(today.getDate()).padStart(2, '0'); 
    let mm = String(today.getMonth() + 1).padStart(2, '0');
    let yyyy = today.getFullYear(); 
    const current_date = dd + '.' + mm + '.' + yyyy;

    const dataset_name_translated = 'test data';
    const dataset_description_translated = 'test kuvaus';
    const dataset_resource_url = "https://example.com"
    const dataset_resource_size = 12345
    const dataset_resource_format = 'CSV'
    const dataset_position_info = "56.7 43.5";
    const dataset_temporal_granularity = "test";
    const dataset_maturity = "current";
    //"29. heinäkuuta 2022" format is used for some fields
    const finnish_month_names = ['tammikuuta', 'helmikuuta', 'maaliskuuta', 'huhtikuuta', 'toukokuuta', 'kesäkuuta',
      'heinäkuuta', 'elokuuta', 'syyskuuta', 'lokakuuta', 'marraskuuta', 'joulukuuta'];
    const simpleday = parseInt(dd, 10)
    const verbose_current_date = simpleday + '. ' + finnish_month_names[today.getMonth()] + ' ' + yyyy;

    const misc_dataset_form_data = {
      '#field-title_translated-fi': misc_dataset_name,
      '#field-notes_translated-fi': misc_dataset_description_if,
      // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: [test_tag]},
      '#field-license_id':{type: 'select', value: 'cc-nc'},
      '#field-maintainer': 'test maintainer',
      '#field-maintainer_email': dataset_maintainer_email,
      '#field-maintainer_website': dataset_maintainer_website,
      '#field-copyright_notice_translated-fi': 'lisenssi test',
      '#field-external_urls': dataset_external_url,
      '#s2id_autogen5': {type: 'select2', values: [dataset_update_interval]},
      '#field-valid_from': {type: 'datepicker', value: valid_from},
      '#field-valid_till': {type: 'datepicker', value: valid_till},
    };

    const misc_dataset_resource_form_data = {
      '#field-name_translated-fi': dataset_name_translated,
      '#field-image-url': dataset_resource_url,
      '#field-size': dataset_resource_size,
      '#field-format': {
        value: dataset_resource_format,
        force: true
      },
      '#field-description_translated-fi': dataset_description_translated,
      '#field-position_info': dataset_position_info,
      '#field-maturity':{type: 'select', value: dataset_maturity},
      // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
      'label[for=field-temporal_granularity-fi] ~ div .select2-choices input': {type: 'select2', values: [dataset_temporal_granularity]},
      '#field-temporal_coverage_to': {type: 'datepicker', value: valid_till},
      '#field-temporal_coverage_from': {type: 'datepicker', value: valid_from},
    };


    before(function(){
      // cy.reset_db()
      // cy.create_organization_for_user(test_organization, 'test-user', true);

      cy.login_post_request('test-user', 'test-user')
      cy.visit('/data/dataset');

      //Manually create the dataset
      cy.get('#second-navbar a[href="/data/fi/dataset"]').click();
      cy.get('a[href="/data/fi/dataset/new"]').click();
      cy.get('.slug-preview button').contains('Muokkaa').click();
      cy.get('#field-name').type(misc_dataset_name);
      cy.fill_form_fields(misc_dataset_form_data);
      cy.get('button[name=save]').click();

      //check that we are on the second form page
      cy.get('.last').should('have.class', 'active');

      cy.contains('a', 'Linkki').click();
      //cy.get('#field-image-upload').selectFile("cypress/FL_insurance_sample.csv");
      cy.fill_form_fields(misc_dataset_resource_form_data);
      cy.get('button[name=save].suomifi-button-primary').click();

      cy.url({timeout: 60000}).should('not.include', `/data/fi/dataset/${misc_dataset_name.replace(" ", "-")}/resource/new`); // after submission is complete, the /resource/new should not be part of the url anymore
      cy.location('pathname').should('contain', `/dataset/${misc_dataset_name.replace(" ", "-")}`);
    });

    beforeEach(function () {
      cy.login_post_request('test-user', 'test-user')
      cy.visit('/');
    });

    it('Dataset collection contains correct properties', function(){
      cy.visit(`/data/fi/dataset/${misc_dataset_name}`);

      cy.get('.dataset-title').should('contain.text', misc_dataset_name);
      cy.get('.notes > p').should('contain.text', misc_dataset_description_if);
      cy.get('.admin-banner > a');
      cy.get('.resource-item').should('contain.text', 'test data');
      cy.get('a.resource-action').should('contain.text', 'Muokkaa');
      cy.get('.resource-url-analytics').should('contain.text', 'Avaa');
    
      //dataset collection information
      cy.get(':nth-child(1) > th').should('contain.text', 'Kokoelma');
      cy.get(':nth-child(2) > th').should('contain.text', 'Ylläpitäjä');

      //collection properties    
      cy.get(':nth-child(1) > td').should('contain.text', 'Avoin data');
      cy.get(':nth-child(2) > td').should('contain.text', test_organization);
      cy.get(':nth-child(3) > .dataset-details').should('contain.text', dataset_maintainer_email);
      cy.get(':nth-child(4) > .dataset-details').should('contain.text', dataset_maintainer_website);
      cy.get(':nth-child(5) > .dataset-details').should('contain.text', dataset_external_url);
      cy.get(':nth-child(6) > .dataset-details').should('contain.text', dataset_update_interval);
      cy.get(':nth-child(7) > .dataset-details').should('contain.text', check_from);
      cy.get(':nth-child(8) > .dataset-details').should('contain.text', check_till);
      cy.get(':nth-child(9) > .dataset-details').should('contain.text', current_date);
      cy.get(':nth-child(10) > .dataset-details').should('contain.text', current_date);

      //tags and licence
      cy.get('.module-content > .tags > .tag-list').should('contain.text', test_tag);
      cy.get(':nth-child(3) > .module-content').should('contain.text', licence_text);
    });

    it('Dataset contains correct properties', function(){
      //open dataset
      cy.visit(`/data/fi/dataset/${misc_dataset_name}`);
      cy.get('.resource-item__info__title').should('contain.text', dataset_name_translated).click();
      cy.location('pathname').should('contain', `/dataset/${misc_dataset_name}/resource/`);

      //breadcrumbs
      cy.get('.breadcrumb > :nth-child(4) > a').should('contain.text', misc_dataset_name);
      cy.get('.breadcrumb > :nth-child(6) > a').should('contain.text', dataset_name_translated);

      //titles 
      cy.get('.module-small-title').should('contain.text', misc_dataset_name);
      cy.get('.page-heading').should('contain.text', dataset_name_translated);
      cy.get('ul > :nth-child(1) > .btn').should('contain.text', 'Muokkaa');
      cy.get('ul > :nth-child(2) > .btn').should('contain.text', 'Avaa');
      //The api button placement might chance, so exclude it for now

      //dataset properties
      cy.get('tbody > :nth-child(1) > :nth-child(2)').should('contain.text', dataset_resource_format);
      cy.get('tbody > :nth-child(2) > :nth-child(2)').should('contain.text', dataset_resource_size);
      cy.get('tbody > :nth-child(3) > :nth-child(2)').should('contain.text', 'Voimassa');
      cy.get('tbody > :nth-child(4) > :nth-child(2)').should('contain.text', dataset_position_info);
      cy.get(':nth-child(5) > :nth-child(2)').should('contain.text', check_from);//easier to check for both separately
      cy.get(':nth-child(5) > :nth-child(2)').should('contain.text', check_till);//easier to check for both separately
      cy.get(':nth-child(6) > :nth-child(2)').should('contain.text', verbose_current_date);
      cy.get(':nth-child(7) > :nth-child(2)').should('contain.text', verbose_current_date);

      cy.get('.secondary > :nth-child(2)').should('contain.text', licence_text)
    });
  });

});
