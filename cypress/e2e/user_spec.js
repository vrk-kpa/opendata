
// User registration
describe('User registration', function() {

    let uuid = require("uuid");
    let weakpassword = "123456"
    let strongpassword = "QWer1234"
    let newpassword = "Newpass1"
    //generate random username and email
    let username = uuid.v4();
    let email = username + "@mail.com" 

    before(function(){
        cy.register(username, email);
      })

    beforeEach(function(){
        cy.visit("/");
    })

    it('Register user and set password', function () {
        //get the body of the registration email
        cy.mhGetAllMails().mhFirst().mhGetBody()
        .then((body) => {
            // parse body for address
            var matches = body.match(/\bhttps?:\/\/\S+/gi);
            if (matches != null){
                //The first link should be the registration link
                cy.visit(matches[0]);
                cy.get('#edit-submit').click();

                cy.get('#edit-pass-pass1').type(weakpassword);
                cy.get('#edit-pass-pass2').type(weakpassword);
                cy.get('.input-group-addon').should('not.exist'); //waits for password policy module to compare the passwords
                cy.get('#edit-submit').click();

                // setting the password should fail
                cy.get('.alert').should('contain.text', 'The password does not satisfy the password policies.');
                cy.get('.alert').should('contain.text', 'Password must contain at least 3 types of characters');
                cy.get('.alert').should('contain.text', 'Password length must be at least 8 characters.');
            
                cy.get('#edit-pass-pass1').type(strongpassword);
                cy.get('#edit-pass-pass2').type(strongpassword);
                cy.get('.input-group-addon').should('not.exist'); //waits for password policy module to compare the passwords
                cy.get('#edit-submit').click();

                cy.get('.alert').should('contain.text', 'Muutokset tallennettiin.');
                cy.get('.form-item-current-pass > .control-label').should('contain.text', 'Nykyinen salasanasi');
                cy.get('#edit-current-pass').should('exist');
            }
            else{
                //fail test if no urls found
                throw new Error("Test failed due to no link found in message body");
            }
          });
    })


    it('Change user password', function(){
        cy.login(username, strongpassword);
        cy.get('[href="/fi/profile"] > span').click();
        cy.get('.module-content > :nth-child(1) > :nth-child(2) > a').click();
        cy.get('#edit-current-pass').type(strongpassword);

        cy.get('#edit-pass-pass1').type(newpassword);
        cy.get('#edit-pass-pass2').type(newpassword);
        cy.get('.input-group-addon').should('not.exist'); //waits for password policy module to compare the passwords
        cy.get('#edit-submit').click();
        cy.get('.alert').should('contain.text', 'Muutokset tallennettiin.');
    })


    it('Empty password field doesnt change the password', function(){
        //use the new password set in the test before
        cy.login(username, newpassword);
        cy.get('[href="/fi/profile"] > span').click();
        cy.get('.module-content > :nth-child(1) > :nth-child(2) > a').click();
        cy.get('#edit-current-pass').type(newpassword);
        //leave the two new password fields empty
        
        cy.get('#edit-submit').click();
        cy.get('.alert').should('contain.text', 'Muutokset tallennettiin.');

        //logout and login again
        cy.logout();
        cy.get('.header-login-link').click();
        cy.get('#edit-name').type(username);
        cy.get('#edit-pass').type(newpassword);
        cy.get('.input-group-addon').should('not.exist'); //waits for password policy module to compare the passwords
        cy.get('#edit-submit').click();
        
    })
  })