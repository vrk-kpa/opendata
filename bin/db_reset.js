const { Client } = require('pg');

const client = new Client({
  user: process.env.DB_CKAN_USER,
  host: process.env.DB_HOST,
  database: process.env.DB_CKAN,
  password: process.env.DB_CKAN_PASS,
  port: 5432,
});

client.connect();


client.query('CREATE OR REPLACE FUNCTION truncate_tables(username IN VARCHAR) RETURNS void AS $$\n' +
  'DECLARE\n' +
  '    statements CURSOR FOR\n' +
  '        SELECT tablename FROM pg_tables\n' +
  '        WHERE tableowner = username AND schemaname = \'public\' AND tablename != \'migrate_version\';\n' +
  'BEGIN\n' +
  '    FOR stmt IN statements LOOP\n' +
  '        EXECUTE \'TRUNCATE TABLE \' || quote_ident(stmt.tablename) || \' CASCADE;\';\n' +
  '    END LOOP;\n' +
  'END;\n' +
  '$$ LANGUAGE plpgsql;', (err, res) => {
  if (err){
    return;
  }
  client.query("SELECT truncate_tables('" + process.env.DB_CKAN + "');", (err, res) => {
    console.log(err, res);
    console.log("truncated");
    client.end()
  });
});

