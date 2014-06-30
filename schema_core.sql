-- This is the schema for the core database.  This database belongs to
-- SSPH.

-- ssph_sp_info describes the known service providers.  A service provider
-- cannot use SSPH unless SSPH has been told to expect it.

CREATE TABLE ssph_sp_info (
	sp	VARCHAR(50) NOT NULL,
		-- name of the service provider.  this name is used in
		-- the incoming URLs
	url	VARCHAR(250) NOT NULL,
		-- url that successful logins are returned to
	dbtype	VARCHAR(20) DEFAULT NULL,
		-- The type of database the *client* uses for the
		-- ssph_auths table.  This is name of a pandokia database
		-- driver module without the "pandokia.db_" in front of it.
		-- That is "XYZ" would perform "import pandokia.db_XYZ"
		--
		-- If NULL, it means the application uses the same database
		-- that this table is in, and dbcreds is ignored.
		-- 
	dbcreds	VARCHAR(250) DEFAULT NULL,
		-- JSON of credentials to access the *client's* database
		-- (i.e. access_arg value for PandokiaDB object)
	expiry	INTEGER DEFAULT 7200,
		-- duration in seconds that new authentications are
		-- cached for this app.  (Though there is currently no
		-- expiration mechanism.)
	contact	VARCHAR(250) NOT NULL,
		-- People responsible for this service provider,
		-- human readable
	email	VARCHAR(250),
		-- email address for contact for this service provider
	confirm_mode CHAR(1) DEFAULT 'd',
		-- 'c' : this SP may use the cgi to confirm authentications
		-- 'd' : this SP uses only database accesses
	secret	VARCHAR(250) DEFAULT NULL,
		-- if confirm_mode = 'c', the shared secret for the handshake
	hash	VARCHAR(10) DEFAULT 'sha1'
		-- if confirm_mode = 'c', the hash to use for the handshake
		-- (the name of the hash from python hashlib)
	);


CREATE UNIQUE INDEX idx_ssph_sp_info
	ON ssph_sp_info ( sp );


-- ssph_auths lists the recently validated authentications.  The client
-- has two options:
--  - if the client record in ssph_sp_info has dbtype of NULL, the table
--    below is used.  The client must have drivers and access to this
--    table in the database used by the ssph server, or must use CGI 
--    confirmation.
--  - if dbtype is the name of a pandokia database driver, then dbcreds
--    are the credentials for the database that the ssph_auths table
--
-- In either case, applications are expected to maintain their own
-- session cookies.  This table gets the application session cookie
-- to the point where the application knows *who* it was issued to.
-- After that, the application ignores the entry in this table.
--
-- The expire here is just for cleaning the database.  If the table
-- is in the ssph database, then ssph is responsible for cleaning
-- it.  If the table is in the client database, then the client is
-- responsible for cleaning it.  (Though no expiration is currently
-- implemented.)
--

CREATE TABLE ssph_auths (
	sp	VARCHAR(50) NOT NULL,
		-- service provider that this record applies to
	cookie	VARCHAR(250) NOT NULL,
		-- session cookie that was authenticated
	info	VARCHAR(8000) NOT NULL,
		-- json of "interesting" data from the SSO
		--  8000 is "maximum allowed for any data type" according to
		--  pymssql; could be larger in other databases.
	expire	INTEGER NOT NULL,
		-- time_t to expire the session cookie.
	idp	VARCHAR(250) NOT NULL,
		-- Identity Provider that performed this authentication
	eppn	VARCHAR(250) NOT NULL
		-- identity of this user
	-- application may place other columns here, as long as
	-- they have DEFAULT or can be NULL.
	);

CREATE UNIQUE INDEX key_authentications 
	on ssph_auths ( sp, cookie );

