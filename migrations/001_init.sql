CREATE TABLE IF NOT EXISTS inventions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  inventors JSONB NOT NULL,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS disclosures (
  id TEXT PRIMARY KEY,
  invention_id TEXT NOT NULL REFERENCES inventions(id),
  text TEXT NOT NULL,
  source TEXT NOT NULL,
  attachments JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
  id TEXT PRIMARY KEY,
  invention_id TEXT NOT NULL REFERENCES inventions(id),
  text TEXT NOT NULL,
  claim_type TEXT NOT NULL,
  status TEXT NOT NULL,
  depends_on JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS spec_sections (
  id TEXT PRIMARY KEY,
  invention_id TEXT NOT NULL REFERENCES inventions(id),
  section_type TEXT NOT NULL,
  text TEXT NOT NULL,
  section_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS figures (
  id TEXT PRIMARY KEY,
  invention_id TEXT NOT NULL REFERENCES inventions(id),
  label TEXT NOT NULL,
  caption TEXT NOT NULL,
  file_ref TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prior_art (
  id TEXT PRIMARY KEY,
  invention_id TEXT NOT NULL REFERENCES inventions(id),
  title TEXT NOT NULL,
  url TEXT,
  publication_date TEXT,
  summary TEXT NOT NULL,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS citations (
  id TEXT PRIMARY KEY,
  invention_id TEXT NOT NULL REFERENCES inventions(id),
  prior_art_id TEXT NOT NULL REFERENCES prior_art(id),
  location TEXT NOT NULL,
  quote TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
  id TEXT PRIMARY KEY,
  invention_id TEXT NOT NULL REFERENCES inventions(id),
  reviewer TEXT NOT NULL,
  decision TEXT NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS document_packages (
  id TEXT PRIMARY KEY,
  invention_id TEXT NOT NULL REFERENCES inventions(id),
  version TEXT NOT NULL,
  artifacts JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS docket_items (
  id TEXT PRIMARY KEY,
  invention_id TEXT NOT NULL REFERENCES inventions(id),
  jurisdiction TEXT NOT NULL,
  due_date TEXT NOT NULL,
  status TEXT NOT NULL,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_disclosures_invention_id ON disclosures(invention_id);
CREATE INDEX IF NOT EXISTS idx_claims_invention_id ON claims(invention_id);
CREATE INDEX IF NOT EXISTS idx_sections_invention_id ON spec_sections(invention_id);
CREATE INDEX IF NOT EXISTS idx_figures_invention_id ON figures(invention_id);
CREATE INDEX IF NOT EXISTS idx_prior_art_invention_id ON prior_art(invention_id);
CREATE INDEX IF NOT EXISTS idx_citations_invention_id ON citations(invention_id);
CREATE INDEX IF NOT EXISTS idx_reviews_invention_id ON reviews(invention_id);
CREATE INDEX IF NOT EXISTS idx_packages_invention_id ON document_packages(invention_id);
CREATE INDEX IF NOT EXISTS idx_docket_invention_id ON docket_items(invention_id);
