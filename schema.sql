CREATE TABLE IF NOT EXISTS analytics_dev.events (
  id                    bigserial PRIMARY KEY,
  event_id              varchar(36) NOT NULL,
  event_timestamp       timestamp NOT NULL,
  event_type            varchar(128) NOT NULL,
  event_version         varchar(12) NOT NULL,
  app_title             varchar(128) NOT NULL,
  app_version           varchar(12) NOT NULL,
  user_id               varchar(128) NOT NULL,
  user_name             varchar(128) NOT NULL,
  created_at            timestamp DEFAULT current_timestamp,
  meta                  jsonb,
  token_payload         jsonb
);
CREATE UNIQUE INDEX IF NOT EXISTS event_id on analytics_dev.events(event_id);
CREATE INDEX IF NOT EXISTS event_type on analytics_dev.events(event_type);

GRANT SELECT, INSERT, UPDATE ON analytics_dev.events TO "producer_dev";
GRANT SELECT ON analytics_dev.events TO "consumer_dev";
GRANT USAGE, SELECT, UPDATE ON analytics_dev.events_id_seq TO "producer_dev";
GRANT USAGE, SELECT ON analytics_dev.events_id_seq TO "consumer_dev";
