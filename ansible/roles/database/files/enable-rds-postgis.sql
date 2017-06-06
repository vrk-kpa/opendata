create extension postgis;
create extension fuzzystrmatch;
create extension postgis_tiger_geocoder;
create extension postgis_topology;

\dn

alter schema tiger owner to rds_superuser;
alter schema topology owner to rds_superuser;

\dn

CREATE FUNCTION exec(text) returns text language plpgsql volatile AS $f$ BEGIN EXECUTE $1; RETURN $1; END; $f$;

SELECT exec('ALTER TABLE ' || quote_ident(s.nspname) || '.' || quote_ident(s.relname) || ' OWNER TO rds_superuser;')
  FROM (
    SELECT nspname, relname
    FROM pg_class c JOIN pg_namespace n ON (c.relnamespace = n.oid)
    WHERE nspname in ('tiger','topology') AND
    relkind IN ('r','S','v') ORDER BY relkind = 'S')
s;

SET search_path=public,tiger;

select na.address, na.streetname, na.streettypeabbrev, na.zip
from normalize_address('1 Devonshire Place, Boston, MA 02109') as na;

select topology.createtopology('my_new_topo',26986,0.5);

ALTER VIEW geometry_columns OWNER TO ckan_default;
ALTER TABLE spatial_ref_sys OWNER TO ckan_default;
