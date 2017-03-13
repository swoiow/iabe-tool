-- face表
CREATE TABLE "face" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL ON CONFLICT ROLLBACK,
    "username" TEXT (12),
    "photo" BLOB,
    "enc_data" TEXT,
    "photo_md5" TEXT (32),
    "photo_type" TEXT (10),
    "used" BLOB (2) DEFAULT - 1,
    "create_date" DATETIME DEFAULT (datetime(CURRENT_TIMESTAMP,'localtime'))
);

-- loger表
CREATE TABLE "loger" (
    "id" INTEGER NOT NULL,
    "type" TEXT (10),
    "logerName" TEXT (20),
    "create_date" DATETIME DEFAULT (datetime(CURRENT_TIMESTAMP,'localtime')),
    "content" TEXT (250),
    PRIMARY KEY ("id" ASC)
);

CREATE INDEX "index_username" ON "loger" (
    "logerName" COLLATE NOCASE ASC
);

-- settings表
CREATE TABLE "settings" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "item" TEXT,
    "itemValue" TEXT
);

-- user 表
ALTER TABLE "users" RENAME TO "_users_update";

DROP INDEX "idx_username";

CREATE TABLE "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "lscode" INTEGER,
    "username" TEXT (80),
    "password" TEXT (20) DEFAULT 1234,
    "create_date" DATETIME DEFAULT (datetime(CURRENT_TIMESTAMP,'localtime')),
    "zone" TEXT (5),
    "is_finish" BOOLEAN DEFAULT 0,
    "responsible" TEXT (30),
    "notes" TEXT
);

INSERT INTO "users" (
    "id", "lscode", "username", "password", "create_date", "zone", "is_finish", "responsible", "notes"
)
SELECT
    "id", "lscode", "username", "password", "create_date", "zone", "is_finish", "responsible", "notes"
    FROM
    "_users_update";

CREATE INDEX "idx_username" ON "users" ("username" COLLATE NOCASE ASC);

DROP TABLE "_users_update"
