CREATE TABLE IF NOT EXISTS dictionary_item (
  item_type     varchar(256),
  item_id       varchar(256),
  name          varchar(1024),
  description   text,
  meta          json,
  PRIMARY KEY (item_type, item_id)
);

CREATE TABLE IF NOT EXISTS link (
  link_type     varchar(256),
  src_item_type varchar(256),
  src_item_id   varchar(256),
  dst_item_type varchar(256),
  dst_item_id   varchar(256),
  CONSTRAINT link_fk1 FOREIGN KEY (src_item_type, src_item_id) REFERENCES dictionary_item(item_type, item_id) ON DELETE CASCADE
);
