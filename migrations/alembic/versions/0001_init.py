"""init schema

Revision ID: 0001_init
Revises: 
Create Date: 2026-02-15 12:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("inventors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "disclosures",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("invention_id", sa.String(), sa.ForeignKey("inventions.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "claims",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("invention_id", sa.String(), sa.ForeignKey("inventions.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("depends_on", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "spec_sections",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("invention_id", sa.String(), sa.ForeignKey("inventions.id"), nullable=False),
        sa.Column("section_type", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False),
    )

    op.create_table(
        "figures",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("invention_id", sa.String(), sa.ForeignKey("inventions.id"), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("file_ref", sa.String(), nullable=False),
    )

    op.create_table(
        "prior_art",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("invention_id", sa.String(), sa.ForeignKey("inventions.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("publication_date", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )

    op.create_table(
        "citations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("invention_id", sa.String(), sa.ForeignKey("inventions.id"), nullable=False),
        sa.Column("prior_art_id", sa.String(), sa.ForeignKey("prior_art.id"), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("invention_id", sa.String(), sa.ForeignKey("inventions.id"), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "document_packages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("invention_id", sa.String(), sa.ForeignKey("inventions.id"), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("artifacts", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "docket_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("invention_id", sa.String(), sa.ForeignKey("inventions.id"), nullable=False),
        sa.Column("jurisdiction", sa.String(), nullable=False),
        sa.Column("due_date", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_index("idx_disclosures_invention_id", "disclosures", ["invention_id"])
    op.create_index("idx_claims_invention_id", "claims", ["invention_id"])
    op.create_index("idx_sections_invention_id", "spec_sections", ["invention_id"])
    op.create_index("idx_figures_invention_id", "figures", ["invention_id"])
    op.create_index("idx_prior_art_invention_id", "prior_art", ["invention_id"])
    op.create_index("idx_citations_invention_id", "citations", ["invention_id"])
    op.create_index("idx_reviews_invention_id", "reviews", ["invention_id"])
    op.create_index("idx_packages_invention_id", "document_packages", ["invention_id"])
    op.create_index("idx_docket_invention_id", "docket_items", ["invention_id"])


def downgrade() -> None:
    op.drop_index("idx_docket_invention_id", table_name="docket_items")
    op.drop_index("idx_packages_invention_id", table_name="document_packages")
    op.drop_index("idx_reviews_invention_id", table_name="reviews")
    op.drop_index("idx_citations_invention_id", table_name="citations")
    op.drop_index("idx_prior_art_invention_id", table_name="prior_art")
    op.drop_index("idx_figures_invention_id", table_name="figures")
    op.drop_index("idx_sections_invention_id", table_name="spec_sections")
    op.drop_index("idx_claims_invention_id", table_name="claims")
    op.drop_index("idx_disclosures_invention_id", table_name="disclosures")

    op.drop_table("docket_items")
    op.drop_table("document_packages")
    op.drop_table("reviews")
    op.drop_table("citations")
    op.drop_table("prior_art")
    op.drop_table("figures")
    op.drop_table("spec_sections")
    op.drop_table("claims")
    op.drop_table("disclosures")
    op.drop_table("inventions")
