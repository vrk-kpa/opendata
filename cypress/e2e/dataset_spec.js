const test_organization = 'dataset_test_organization';

describe('Dataset sorting tests', function(){

  const dataset_name_1 = "first_dataset";
  const dataset_name_2 = "second_dataset";

  before(function(){
    cy.reset_db();
    cy.create_organization_for_user(test_organization, 'test-user', true);
    cy.login_post_request('test-user', 'test-user')
    cy.visit('/data/dataset');
    cy.create_new_dataset(dataset_name_1);
    cy.create_new_dataset(dataset_name_2);
  });

  it('Dataset default sorting option is empty', function(){
    cy.visit('/data/dataset');
    cy.get('#field-order-by').should('have.value', 'auto');

  });

  it('Dataset default sorting option is empty after search', function(){
    cy.visit('/data/dataset');
    cy.get('.search').type('random search');
    cy.get('.fal').click();
    cy.get('#field-order-by').should('have.value', 'auto');
  });

  it('Dataset chosen sorting option persists after search', function(){
    cy.visit('/data/dataset');
    cy.get('#field-order-by').select('score desc, metadata_modified desc');
    // wait for url to contain the updated sorting option
    cy.url().should('include', `sort=score+desc%2C+metadata_modified+desc`); //wait for page load after choosing sorting option
    cy.get('.search').type('random search');
    cy.get('.fal').click();
    cy.url().should('include', `sort=score+desc%2C+metadata_modified+desc`); //wait for page load after choosing sorting option
    cy.get('#field-order-by').should('have.value', 'score desc, metadata_modified desc');
  });

  it('Datasets have sorting options', function(){
    cy.visit('/data/dataset');
    cy.get('#field-order-by > option').eq(0).should('have.value', 'auto');
    cy.get('#field-order-by > option').eq(1).should('have.value', 'score desc, metadata_modified desc');
    cy.get('#field-order-by > option').eq(2).should('have.value', 'title_string asc');
    cy.get('#field-order-by > option').eq(3).should('have.value', 'title_string desc');
    cy.get('#field-order-by > option').eq(4).should('have.value', 'metadata_modified desc');
    cy.get('#field-order-by > option').eq(5).should('have.value', 'metadata_created asc');
    cy.get('#field-order-by > option').eq(6).should('have.value', 'metadata_created desc');
    cy.get('#field-order-by > option').eq(7).should('have.value', 'views_recent desc');
  });

  it('Dataset advanced search has sorting options', function(){
    cy.visit('/data/dataset');

    cy.get('.mb-2 > .btn-avoindata-header').click();

    cy.get('#field-order-by > option').eq(0).should('have.value', 'auto');
    cy.get('#field-order-by > option').eq(1).should('have.value', 'score desc, metadata_modified desc');
    cy.get('#field-order-by > option').eq(2).should('have.value', 'title_string asc');
    cy.get('#field-order-by > option').eq(3).should('have.value', 'title_string desc');
    cy.get('#field-order-by > option').eq(4).should('have.value', 'metadata_modified desc');
    cy.get('#field-order-by > option').eq(5).should('have.value', 'metadata_created asc');
    cy.get('#field-order-by > option').eq(6).should('have.value', 'metadata_created desc');
    cy.get('#field-order-by > option').eq(7).should('have.value', 'views_recent desc');
  });

  it('Datasets are sorted by creation date by default', function(){  
    // check if the ordering is correct (creation date desc)
    cy.visit('/data/dataset');
    cy.get(':nth-child(1) > .dataset-content > .align-items-center > .dataset-heading > a').should('have.text', dataset_name_2);
    cy.get(':nth-child(2) > .dataset-content > .align-items-center > .dataset-heading > a').should('have.text', dataset_name_1);

    // change the sorting to creation date asc
    cy.get('#field-order-by').select('metadata_created asc');
    cy.url().should('include', `sort=metadata_created+asc`); //wait for page load after choosing sorting option

    cy.get(':nth-child(1) > .dataset-content > .align-items-center > .dataset-heading > a').should('have.text', dataset_name_1);
    cy.get(':nth-child(2) > .dataset-content > .align-items-center > .dataset-heading > a').should('have.text', dataset_name_2);
  });

  it('Dataset properties are visible as filter options', function(){
    cy.visit('/data/dataset');

    cy.get(':nth-child(4) > nav > .list-unstyled > .nav-item > a > span').should('have.text', "Avoin data (2)");
    cy.get(':nth-child(5) > nav > .list-unstyled > .nav-item > a > span').should('have.text', "test_keyword (2)");
    //look for partial text as the organization can have an ID suffix 
    cy.get(':nth-child(6) > nav > .list-unstyled > .nav-item > a > span').should('include.text', "dataset_test_organization"); 
    cy.get(':nth-child(8) > nav > .list-unstyled > .nav-item > a > span').should('have.text', "Lisenssiä ei ole määritelty (2)")
  });

});


describe('Dataset creation tests', function() {
  beforeEach(function () {
    cy.login_post_request('test-user', 'test-user')
    cy.visit('/');
    cy.get('nav a[href="/data/fi/dataset"]').click();
  })

  it("Create minimal dataset and add file as a resource", function(){
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
      cy.location('pathname', {timeout: 20000}).should('not.include', '/resource/new');
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
  })

  it('Creating an empty dataset fails', function() {
    cy.get('a[href="/data/fi/dataset/new"]').click();
    cy.get('button[name=save]').click();
    cy.get('.error-explanation');
  })

  it('Cannot create dataset if logged out', function() {
    cy.logout_request();
    cy.visit('/');
    cy.get('nav a[href="/data/fi/dataset"]').click();
    cy.get('a[href="/data/fi/dataset/new"]').should('not.exist');
  })
})

describe('Miscellaneous dataset tests', function(){

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
    '#field-description_translated-fi': dataset_description_translated,
    '#field-position_info': dataset_position_info,
    '#field-maturity':{type: 'select', value: dataset_maturity},
    // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
    'label[for=field-temporal_granularity-fi] ~ div .select2-choices input': {type: 'select2', values: [dataset_temporal_granularity]},
    '#field-temporal_coverage_to': {type: 'datepicker', value: valid_till},
    '#field-temporal_coverage_from': {type: 'datepicker', value: valid_from},
  };


  before(function(){
    cy.reset_db()
    cy.create_organization_for_user(test_organization, 'test-user', true);


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
    cy.get('.last', {timeout: 20000}).should('have.class', 'active');

    cy.get('#field-image-upload').selectFile("cypress/FL_insurance_sample.csv");
    cy.fill_form_fields(misc_dataset_resource_form_data);
    cy.get('button[name=save].suomifi-button-primary').click();

    cy.url({timeout: 60000}).should('not.include', `/data/fi/dataset/${misc_dataset_name.replace(" ", "-")}/resource/new`); // after submission is complete, the /resource/new should not be part of the url anymore
    cy.location('pathname', {timeout: 20000}).should('contain', `/dataset/${misc_dataset_name.replace(" ", "-")}`);
  });

  beforeEach(function () {
    cy.login_post_request('test-user', 'test-user')
    cy.visit('/');
  });

  it('Created datasets are visible on users profile', function(){
    cy.visit('/data/dataset');
    cy.get('[href="/fi/profile"] > span').click();
    cy.get(':nth-child(1) > .dataset-content > .align-items-center > .dataset-heading > a').should('have.text', misc_dataset_name);
  });

  
  it('Dataset can be opened from the profile page', function(){
    cy.get('[href="/fi/profile"] > span').click();
    cy.get(':nth-child(1) > .dataset-content > .align-items-center > .dataset-heading > a').should('contain.text', misc_dataset_name).click();
    cy.location('pathname', {timeout: 20000}).should('contain', `/dataset/${misc_dataset_name}`);
    cy.get('.dataset-title').should('contain.text', misc_dataset_name);
    cy.get('.notes > p').should('contain.text', misc_dataset_description_if);

    //open dataset 
    cy.get('.resource-item__info__title').should('contain.text', 'test data').click();
    cy.location('pathname', {timeout: 20000}).should('contain', `/dataset/${misc_dataset_name}/resource`);
  });

  it('Dataset collection contains correct properties', function(){
    // open dataset collection
    cy.get('.opendata-menu-container > .nav > :nth-child(2) > a').click();
    cy.get(':nth-child(1) > .dataset-content > .align-items-center > .dataset-heading > a').should('contain.text', misc_dataset_name).click();
    cy.location('pathname', {timeout: 20000}).should('contain', `/dataset/${misc_dataset_name}`);
    cy.get('.dataset-title').should('contain.text', misc_dataset_name);
    cy.get('.notes > p').should('contain.text', misc_dataset_description_if);
    cy.get('.admin-banner > a');
    cy.get('.resource-item').should('contain.text', 'test data');
    cy.get('a.resource-action').should('contain.text', 'Muokkaa');
    cy.get('.resource-url-analytics').should('contain.text', 'Lataa');
  
    //dataset collection information
    cy.get(':nth-child(1) > th').should('contain.text', 'Kokoelma');
    cy.get(':nth-child(2) > th').should('contain.text', 'Ylläpitäjä');

    //collection properties    
    cy.get(':nth-child(1) > td').should('contain.text', 'Avoin data');
    cy.get(':nth-child(2) > td').should('contain.text', test_organization);
    cy.get(':nth-child(3) > .dataset-details').should('contain.text', dataset_maintainer_email);
    cy.get(':nth-child(4) > .dataset-details').should('contain.text', dataset_maintainer_website);
    cy.get(':nth-child(5) > .dataset-details').should('contain.text', dataset_external_url);
    cy.get(':nth-child(7) > .dataset-details').should('contain.text', dataset_update_interval);
    cy.get(':nth-child(8) > .dataset-details').should('contain.text', check_from);
    cy.get(':nth-child(9) > .dataset-details').should('contain.text', check_till);
    cy.get(':nth-child(10) > .dataset-details').should('contain.text', current_date);
    cy.get(':nth-child(11) > .dataset-details').should('contain.text', current_date);

    //tags and licence
    cy.get('.module-content > .tags > .tag-list').should('contain.text', test_tag);
    cy.get(':nth-child(3) > .module-content').should('contain.text', licence_text);
  });

  it('Dataset contains correct properties', function(){
    //open dataset
    cy.get('.opendata-menu-container > .nav > :nth-child(2) > a').click();
    cy.get(':nth-child(1) > .dataset-content > .align-items-center > .dataset-heading > a').should('contain.text', misc_dataset_name).click();
    cy.location('pathname', {timeout: 20000}).should('contain', `/dataset/${misc_dataset_name}`);
    cy.get('.resource-item__info__title').should('contain.text', dataset_name_translated).click();
    cy.location('pathname', {timeout: 20000}).should('contain', `/dataset/${misc_dataset_name}/resource/`);

    //breadcrumbs
    cy.get('.breadcrumb > :nth-child(4) > a').should('contain.text', misc_dataset_name);
    cy.get('.breadcrumb > :nth-child(6) > a').should('contain.text', dataset_name_translated);

    //titles 
    cy.get('.module-small-title').should('contain.text', misc_dataset_name);
    cy.get('.page-heading').should('contain.text', dataset_name_translated);
    cy.get('ul > :nth-child(1) > .btn').should('contain.text', 'Muokkaa');
    cy.get('ul > :nth-child(2) > .btn').should('contain.text', 'Lataa');
    //The api button placement might chance, so exclude it for now

    //dataset properties
    //cloud storage treats the extensions a bit differently compared to local tests
    if (Cypress.env('cloudStorageEnabled')){
      cy.get('tbody > :nth-child(1) > :nth-child(2)').should('contain.text', 'CSV');
    }else{
      cy.get('tbody > :nth-child(1) > :nth-child(2)').should('contain.text', 'text/csv');
    }
    cy.get('tbody > :nth-child(2) > :nth-child(2)').should('contain.text', '4123652'); //filesize of the uploaded file
    cy.get('tbody > :nth-child(3) > :nth-child(2)').should('contain.text', 'Voimassa');
    cy.get('tbody > :nth-child(4) > :nth-child(2)').should('contain.text', dataset_position_info);
    cy.get(':nth-child(5) > :nth-child(2)').should('contain.text', check_from);//easier to check for both separately
    cy.get(':nth-child(5) > :nth-child(2)').should('contain.text', check_till);//easier to check for both separately
    cy.get(':nth-child(6) > :nth-child(2)').should('contain.text', verbose_current_date);
    cy.get(':nth-child(7) > :nth-child(2)').should('contain.text', verbose_current_date);

    cy.get('.secondary > :nth-child(2)').should('contain.text', licence_text)
  });

  it('Delete a dataset', function(){
    cy.visit('/data/fi/dataset');
    cy.get(`a[href="/data/fi/dataset/${misc_dataset_name}"]`).click();
    cy.edit_dataset(misc_dataset_name);
    cy.delete_dataset(misc_dataset_name);
  });

  it('Deleted datasets are not visible on users profile', function(){
    cy.visit('/data/dataset');
    cy.get('[href="/fi/profile"] > span').click();
    cy.get('.primary > .module > .module-content > .empty').should('contain.text', 'Käyttäjä ei ole luonut tietoaineistoja.');
  });

});