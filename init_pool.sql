DROP DATABASE projectb;
CREATE DATABASE projectb;

\c projectb

CREATE TABLE archive (
       id SERIAL PRIMARY KEY,
       name TEXT UNIQUE NOT NULL,
       origin_server TEXT,
       description TEXT
);

CREATE TABLE component (
       id SERIAL PRIMARY KEY,
       name TEXT UNIQUE NOT NULL,
       description TEXT,
       meets_dfsg BOOLEAN
);

CREATE TABLE architecture (
       id SERIAL PRIMARY KEY,
       arch_string TEXT UNIQUE NOT NULL,
       description TEXT
);

CREATE TABLE maintainer (
       id SERIAL PRIMARY KEY, 
       name TEXT UNIQUE NOT NULL
);

CREATE TABLE location (
       id SERIAL PRIMARY KEY,
       path TEXT NOT NULL,
       component INT4 REFERENCES component,
       archive INT4 REFERENCES archive,
       type TEXT NOT NULL
);

-- No references below here to allow sane population; added post-population

CREATE TABLE files (
       id SERIAL PRIMARY KEY,
       filename TEXT NOT NULL,
       size INT8 NOT NULL,
       md5sum TEXT NOT NULL,
       location INT4 NOT NULL, -- REFERENCES location
       last_used TIMESTAMP,
       unique (filename, location)
);

CREATE TABLE source (
        id SERIAL PRIMARY KEY,
        source TEXT NOT NULL,
        version TEXT NOT NULL,
        maintainer INT4 NOT NULL, -- REFERENCES maintainer
        file INT4 UNIQUE NOT NULL, -- REFERENCES files
	unique (source, version)
);

CREATE TABLE dsc_files (
       id SERIAL PRIMARY KEY,
       source INT4 NOT NULL, -- REFERENCES source,
       file INT4 NOT NULL, -- RERENCES files
       unique (source, file)
);

CREATE TABLE binaries (
       id SERIAL PRIMARY KEY,
       package TEXT NOT NULL,
       version TEXT NOT NULL,
       maintainer INT4 NOT NULL, -- REFERENCES maintainer
       source INT4, -- REFERENCES source,
       architecture INT4 NOT NULL, -- REFERENCES architecture
       file INT4 UNIQUE NOT NULL, -- REFERENCES files,
       type TEXT NOT NULL,
-- joeyh@ doesn't want .udebs and .debs with the same name, which is why the unique () doesn't mention type
       unique (package, version, architecture)
);

CREATE TABLE suite (
       id SERIAL PRIMARY KEY,
       suite_name TEXT NOT NULL,
       version TEXT NOT NULL,
       origin TEXT,
       label TEXT,
       policy_engine TEXT,
       description TEXT
);
  
CREATE TABLE suite_architectures (
       suite INT4 NOT NULL, -- REFERENCES suite
       architecture INT4 NOT NULL, -- REFERENCES architecture
       unique (suite, architecture)
);
            
CREATE TABLE bin_associations (
       id SERIAL PRIMARY KEY,
       suite INT4 NOT NULL, -- REFERENCES suite
       bin INT4 NOT NULL, -- REFERENCES binaries
       unique (suite, bin)
);

CREATE TABLE src_associations (
       id SERIAL PRIMARY KEY,
       suite INT4 NOT NULL, -- REFERENCES suite
       source INT4 NOT NULL, -- REFERENCES source
       unique (suite, source)
);

CREATE TABLE section (
       id SERIAL PRIMARY KEY,
       section TEXT UNIQUE NOT NULL
);

CREATE TABLE priority (
       id SERIAL PRIMARY KEY,
       priority TEXT UNIQUE NOT NULL,
       level INT4 UNIQUE NOT NULL
);

CREATE TABLE override_type (
       id SERIAL PRIMARY KEY,
       type TEXT UNIQUE NOT NULL
);

CREATE TABLE override (
       package TEXT NOT NULL, 
       suite INT4 NOT NULL, -- references suite
       component INT4 NOT NULL, -- references component
       priority INT4, -- references priority
       section INT4 NOT NULL, -- references section
       type INT4 NOT NULL, -- references override_type
       maintainer TEXT,
       unique (suite, component, package, type)
);

-- Critical indexes

CREATE INDEX bin_associations_bin ON bin_associations (bin);
CREATE INDEX src_associations_source ON src_associations (source);
CREATE INDEX source_maintainer ON source (maintainer);
CREATE INDEX binaries_maintainer ON binaries (maintainer);
CREATE INDEX dsc_files_file ON dsc_files (file);
