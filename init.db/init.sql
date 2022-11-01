CREATE TABLE IF NOT EXISTS "apiuser" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "login" VARCHAR(30) NOT NULL UNIQUE,
    "password" VARCHAR(64) NOT NULL,
    "salt" VARCHAR(10) NOT NULL,
    "activate_token" VARCHAR(20),
    "private_token" VARCHAR(660),
    "is_active" BOOL NOT NULL  DEFAULT False,
    "is_admin" BOOL NOT NULL  DEFAULT False
);
CREATE TABLE IF NOT EXISTS "account" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "balance" BIGINT NOT NULL  DEFAULT 0,
    "owner_id" INT NOT NULL REFERENCES "apiuser" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "commodity" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(30) NOT NULL,
    "description" TEXT NOT NULL,
    "price" BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS "transaction" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "value" BIGINT NOT NULL,
    "tx_id" BIGINT NOT NULL,
    "timestamp" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "account_from_id" INT NOT NULL REFERENCES "account" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_transaction_account_e74600" UNIQUE ("account_from_id", "tx_id")
);
