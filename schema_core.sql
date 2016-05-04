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
	contact	VARCHAR(250) NOT NULL,
		-- People responsible for this service provider,
		-- human readable
	email	VARCHAR(250),
		-- email address for contact for this service provider
	secret	VARCHAR(250) DEFAULT NULL,
		-- if confirm_mode = 'c', the shared secret for the handshake
	hash	VARCHAR(10) DEFAULT 'sha1'
		-- if confirm_mode = 'c', the hash to use for the handshake
		-- (the name of the hash from python hashlib)
	);


CREATE UNIQUE INDEX idx_ssph_sp_info
	ON ssph_sp_info ( sp );


-- ssph_auth_events is a log of all authentication events.  This table
-- exists in the main SSPH database, where it logs all successful events
-- that come by.  If the SP uses database-based authentication, then
-- this identical table must exist in the SP database, and the 
-- authentication event is also inserted there.

-- The client has two options:
--
--	dbtype='ssph'
--		The SP must use the CGI validator to check authentication
--		events.  This table only exists in the SSPH database.
--
--	dbtype=anything else
--		The SP looks at its own table for validation
--		authentication events.  dbtype is the name of the
--		pandokia driver with "db_" taken off the front.
--
-- In either case, applications are expected to maintain their own
-- session cookies.  The auth_event_id is *not* a session cookie;
-- the SP must make their own crypto-strong session cookie and issue
-- it to the user.  One the SP has issued the user a session cookie,
-- the record in this table is only useful as a log entry.
--

CREATE TABLE ssph_auth_events (
	tyme		CHAR(26) 	NOT NULL,
			-- datetime.datetime.utcnow().isoformat(' ')
	sp		VARCHAR(50) 	NOT NULL,
			-- name of the SP
	auth_event_id 	VARCHAR(128) 	NOT NULL,
			-- see get_auth_event_id()
	client_ip	VARCHAR(45) 	NOT NULL,
			-- text representation
	idp		VARCHAR(250) 	NOT NULL,
	stsci_uuid		VARCHAR(250) 	NOT NULL,
	attribs		VARCHAR(8000) 	NOT NULL,
			-- json of "interesting" data from the SSO
			--  8000 is "maximum allowed for any data type" according to
			--  pymssql; could be larger in other databases.
	consumed	CHAR(1) 	NOT NULL DEFAULT 'N'
			-- Possible values are:
			--	N	the SP has not checked this event
			--	Y	the SP has checked this event
			--	E	the SP checked this event after it expired
			--	D	the SP uses Database Confirmation, so CGI 
			--		confirmation should never work
	);

create index ssph_auth_events_id on
	ssph_auth_events ( auth_event_id );

