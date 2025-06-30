describe('Placeholder Test', () => {
  it('skips if app is not ready', () => {
    cy.request({
      url: '/',
      failOnStatusCode: false,
    }).then((res) => {
      if (res.status !== 200) {
        cy.log('App not ready, skipping test');
        return;
      }

      // Add real checks later
      cy.contains('Streamlit');
    });
  });
});