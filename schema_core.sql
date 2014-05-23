-- This is the schema for the core database.  This database belongs to
-- SSPH.

CREATE TABLE sp_info (
	sp	VARCHAR,
		-- name of the application
	url	VARCHAR,
		-- url that successful logins are returned to
	dbtype	VARCHAR,
		-- type of database the client uses
		--  name of a supported pandokia database driver
		-- 
	dbcreds	VARCHAR,
		-- JSON of credentials to access the client database
		-- (i.e. access_arg value for PandokiaDB object)
	expiry	INTEGER DEFAULT 7200,
		-- seconds that authentications are cached for this app
	contact	VARCHAR(255)
		-- STScI contacts for this service provider, human readable
	);

CREATE UNIQUE INDEX idx_sp_info
	ON sp_info ( sp );

--
-- This is the table of authenticated session cookies.  This table exists
-- in the core database that belongs to SSPH so that applications need
-- not 1) keep their own database for this information, or 2) maintain
-- expirations in this table.
--
-- In either case, applications are expected to recognize expired cookies
-- on their own.
--

CREATE TABLE ssph_auths (
	sp	VARCHAR,
		-- service provider that this record applies to
	cookie	VARCHAR,
		-- session cookie that was authenticated
	blob	VARCHAR,
		-- json blob of "interesting" data
	expire	INTEGER
		-- time_t to expire the session cookie.
	-- application may place other columns here, as long as
	-- they have DEFAULT or are not "NOT NULL"
	);

CREATE UNIQUE INDEX key_authentications 
	on ssph_auths ( sp, cookie );

