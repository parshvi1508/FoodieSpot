# Database schema
-- schema.sql
CREATE TABLE restaurants (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    capacity INT NOT NULL,
    cuisine TEXT NOT NULL
);

CREATE TABLE reservations (
    id UUID PRIMARY KEY,
    restaurant_id UUID REFERENCES restaurants(id),
    user_email TEXT NOT NULL,
    time TIMESTAMPTZ NOT NULL
);
