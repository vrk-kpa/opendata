// 6. Käyttäjä valitsee haluamansa kielen
it('Käyttäjä valitsee haluamansa kielen', function() {
    cy.visit('/')
    cy.login('test-user', 'test-user');
    cy.login_post_request('test-user', 'test-user');
    //cy.visit('data/fi/user/test-user');
    // cy.get('nav a[href="/data/fi/dataset"]').click();
    cy.contains('Tietoaineistot').click()
    // cy.visit('block-avoindata-mainnavigationfi-menu').should(contains(Tietoaineistot))).click()
    cy.contains('Minun tietoaineistoni').click()
    //cy.visit('fi/user/40/edit')
    cy.contains('Käyttäjätilin asetukset').click()
    // Change language to Swedish
    //cy.get('select')(1).click(); 
    cy.get('select').eq(0).select('sv').should('have.value', 'sv') //[name="preferred_langcode"]').click();
    // Save selected
    cy.get('button[name="op"]').click();
    // Frontpage
    cy.visit('/');
    // cy.get('nav a[href="/data/fi/dataset"]').click();
    cy.contains('Tietoaineistot').click()
    // cy.visit('block-avoindata-mainnavigationfi-menu').should(contains(Tietoaineistot))).click()
    cy.contains('Minun tietoaineistoni').click()
    //cy.visit('fi/user/40/edit')
    cy.contains('Käyttäjätilin asetukset').click()
    // Change lanquage to English
    //select-wrapper option value
    cy.get('select').eq(0).select('en').should('have.value', 'en') //[name="preferred_langcode"]').click();
    // Save selected
    cy.get('button[name="op"]').click();
    // Frontpage
    cy.visit('/');
    // Frontpage
    cy.visit('/');
    // cy.get('nav a[href="/data/fi/dataset"]').click();
    cy.contains('Tietoaineistot').click()
    // cy.visit('block-avoindata-mainnavigationfi-menu').should(contains(Tietoaineistot))).click()
    cy.contains('Minun tietoaineistoni').click()
    //cy.visit('fi/user/40/edit')
    cy.contains('Käyttäjätilin asetukset').click()
    // Change lanquage back to Finnish
    //select-wrapper option value
    cy.get('select').eq(0).select('fi').should('have.value', 'fi') //[name="preferred_langcode"]').click();
    // Save selected
    cy.get('button[name="op"]').click();
    // Frontpage
    cy.visit('/');
    // Logout
    cy.logout(); 
})

// 7. Käyttäjä tarkastelee tietosisältöjä
it('Käyttäjä tarkastelee tietosisältöjä', function() {
    cy.visit('/');
    cy.login('test-user', 'test-user');
    cy.login_post_request('test-user', 'test-user');
    cy.visit('/data/fi/dataset');
    cy.visit('/data/fi/dashboard/datasets');
    // cy.get('.btn-avoindata-header').contains('Minun tietoaineistoni').click();
    // btn-avoindata-header
    cy.contains('Oma profiili').click();
    // cy.visit('/data/fi/user/test-user'); // Oma profiili  Suora linkki
    cy.contains('Muokkaa henkilötietojasi').click();
    // cy.visit('/data/fi/user/edit/test-user');  // Muokkaa henkilötietojasi  Suora linkki
    cy.go('back')
    cy.contains('Ajankohtaista').click();
    // cy.visit('/data/fi/dashboard');   // Ajankohtaista
    cy.go('back')
    cy.contains('Minun tuottajani').click();
    // cy.visit('/data/fi/dashboard/organizations');   //  Minun tuottajani
    cy.go('back')
    cy.contains('Minun tietoaineistoni').click();
    // cy.visit('/data/fi/dashboard/datasets');   //  Minun tietoaineistoni    
    cy.go('back')
    cy.contains('Käyttäjätilin asetukset').click();
    cy.visit('/');  
    cy.logout();  
})

  // 9. Käyttäjä syöttää tietoaineiston tiedot manuaalisesti // testi löytyy dataset_spec.js osasta
  it('Käyttäjä syöttää tietoaineiston tiedot manuaalisesti', function() {
    //    cy.reset_db();
    
    function url_Alpha_Numeric() {
        var text = "";
        var possible = "abcdefghijklmnopqrstuvwxyz0123456789";
      
        for (var i = 0; i < 10; i++)
          text += possible.charAt(Math.floor(Math.random() * possible.length));
      
        return text;
      }
    
      cy.visit('/')
        cy.login('test-user', 'test-user');
        cy.login_post_request('test-user', 'test-user');
        cy.visit('/data/fi/dataset')
        cy.get('a[href="/data/fi/dataset/new"]').click();
        
        
        const dataset_name = 'test_dataset'+ (url_Alpha_Numeric());
           cy.create_new_dataset(dataset_name);
   
    
        const dataset_form_data = {
            "#field-title_translated-fi": dataset_name,
            '#field-notes_translated-fi': 'Dataset test description',
            '#s2id_autogen1': 'test_keyword {enter}',
            '#field-maintainer': 'test maintainer',
            '#field-maintainer_email': 'test.maintainer@example.com'
          };      

         cy.logout();  
    })

// 22. Käyttäjä luo uuden sisältösivun
it('Käyttäjä luo uuden sisältösivun', function() {
  cy.visit('/')
  cy.login('test-publisher', 'test-publisher');
  cy.login_post_request('test-publisher', 'test-publisher');
  cy.visit('/')
  cy.visit('/fi/admin/content')
  cy.visit('/fi/node/add')
  // Lisätään uusi uutinen
  cy.contains('Avoindata Article').click();
  //cy.visit('/fi/node/add/avoindata_article')

  const news_name = 'news_test';
  const news_form_data = {
   "#edit-title-0-value": 'news_name',                                      // uutisen nimi
   '#id=editlangcode-0-value': 'Kielivalinta',                              // Kielivalinta
   '#cke_wysiwyg_frame cke_reset': 'tähän tulee juttua {enter}',            // Uutinen
   '#field-maintainer': '',                                                    // Liitetiedosto
   '#edit-field-tags-target-id': 'Helsinki, Turku, Tampere, Hämeenlinna'       // Tagit
  };

  // Title field
  cy.get('#edit-title-0-value').click({force:true}).type(news_name)

  // Lanquage id=editlangcode-0-value //select[@id='edit-langcode-0-value']
  cy.get('#edit-langcode-0-value').select('fi', {force: true})

  // Body - input text here   //iframe[@class='cke_wysiwyg_frame cke_reset']
  //cy.get('a[href="fi/node/add/avoindata_article"]').click
  
  // Image  //input[@id='edit-field-image-0-upload']
  // cy.get('#edit-field-image-0-upload').then(function(subject){
  // cy.fixture("FL_insurance_sample.csv", 'base64')
  // .then(Cypress.Blob.base64StringToBlob)
  // .then(function(blob){
  //  const el = subject[0];
  //   const testFile = new File([blob],"FL_insurance_sample.csv", {type: 'CSV'} );
  //   const dataTranfer = new DataTransfer();
  //   dataTranfer.items.add(testFile);
  //   el.files = dataTranfer.files;
  //  cy.wrap(subject).trigger('change', { force: true });
    

  // Tags   //input[@id='edit-field-tags-target-id']
  cy.get('#edit-field-tags-target-id').click({force: true}).type('test')
  
  // Save
  cy.contains('Tallenna').click()
    
  cy.visit('/')
  cy.logout();    
})

// 38. Käyttäjä selaa tapahtumia
it('Käyttäjä selaa tapahtumia', function() {
    cy.visit('/')
    cy.login('test-user', 'test-user');
    cy.login_post_request('test-user', 'test-user');
    // cy.visit('/')
    cy.visit('/data/fi/organization')
    // cy.visit('/data/fi/member-request/mylist')
    cy.get('.btn-group').contains('Omat jäsenyyteni').click();
    cy.go('back')
    // cy.visit('/data/fi/member-requests/list')
    cy.contains('Jäsenhakemukset').click();
    cy.go('back')
    cy.contains('Yksityishenkilö').click();
    // cy.visit('/data/fi/organization/yksityishenkilö')
    cy.contains('Tietoaineistot').click();
    
        
    cy.logout();  
})


// 38. Pääkäyttäjä selaa tapahtumia
it('Pääkäyttäjä selaa tapahtumia', function() {
    cy.visit('/')
    //cy.login('test-user', 'test-user');
    cy.login_post_request('admin', 'administrator');
    // cy.visit('/')
    cy.visit('/data/fi/organization')
    // cy.visit('/data/fi/user_list')
    cy.get('.btn-group').contains('Käyttäjät').click();
    //cy.get('td.media').contains('test-user').click();
    cy.visit('/data/fi/user/test-user');
    cy.visit('/data/fi/user_list');
    cy.go('back')
    cy.contains('Tapahtumatiedot').click();
    cy.contains('Data Requests').click();
    cy.go('back')
    cy.contains('Tietoaineistot').click();
        
    cy.logout();  
})
