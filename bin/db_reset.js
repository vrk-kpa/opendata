const { Client } = require('pg');

const client = new Client({
  user: 'ckan_test',
  host: '10.10.10.10',
  database: 'ckan_test',
  password: 'pass',
  port: 5432,
});

client.connect();


client.query('CREATE OR REPLACE FUNCTION truncate_tables(username IN VARCHAR) RETURNS void AS $$\n' +
  'DECLARE\n' +
  '    statements CURSOR FOR\n' +
  '        SELECT tablename FROM pg_tables\n' +
  '        WHERE tableowner = username AND schemaname = \'public\';\n' +
  'BEGIN\n' +
  '    FOR stmt IN statements LOOP\n' +
  '        EXECUTE \'TRUNCATE TABLE \' || quote_ident(stmt.tablename) || \' CASCADE;\';\n' +
  '    END LOOP;\n' +
  'END;\n' +
  '$$ LANGUAGE plpgsql;', (err, res) => {
  console.log(err, res)
  //client.end()
});


client.query("SELECT truncate_tables('ckan_test');", (err, res) => {
  console.log(err, res);
  console.log("trucated");
  client.end()
});
