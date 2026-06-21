-- FinSafe Personal Finance Tracker
-- Run this to create tables manually (app uses Flask-Migrate in practice)

CREATE TABLE IF NOT EXISTS "user" (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(80)  UNIQUE NOT NULL,
    email       VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS category (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    user_id    INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    color      VARCHAR(7) DEFAULT '#6c757d',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, user_id)
);

CREATE TABLE IF NOT EXISTS expense (
    id          SERIAL PRIMARY KEY,
    amount      DECIMAL(10, 2) NOT NULL,
    description VARCHAR(255) NOT NULL,
    date        DATE NOT NULL DEFAULT CURRENT_DATE,
    user_id     INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES category(id),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS income (
    id          SERIAL PRIMARY KEY,
    amount      DECIMAL(10, 2) NOT NULL,
    description VARCHAR(255) NOT NULL,
    date        DATE NOT NULL DEFAULT CURRENT_DATE,
    source      VARCHAR(100),
    user_id     INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budget (
    id              SERIAL PRIMARY KEY,
    amount          DECIMAL(10, 2) NOT NULL,
    period          VARCHAR(20) NOT NULL,   -- 'monthly', 'weekly', 'yearly'
    month           INTEGER,                -- 1-12 for monthly budgets
    year            INTEGER,
    alert_threshold DECIMAL(5, 2) DEFAULT 80.0,
    user_id         INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    category_id     INTEGER REFERENCES category(id),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS savings_goal (
    id             SERIAL PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    target_amount  DECIMAL(10, 2) NOT NULL,
    current_amount DECIMAL(10, 2) DEFAULT 0.0,
    target_date    DATE,
    user_id        INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at     TIMESTAMP DEFAULT NOW(),
    updated_at     TIMESTAMP DEFAULT NOW()
);
