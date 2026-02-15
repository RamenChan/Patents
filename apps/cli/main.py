from __future__ import annotations

import argparse

from patents.domain import models
from patents.infra.memory import InMemoryRepository, SystemClock, UuidGenerator
from patents.infra.renderer import SimpleTextRenderer
from patents.infra.storage import InMemoryStorage
from patents.usecases.assemble_ids import AssembleIDS, AssembleIdsInput
from patents.usecases.compose_spec import ComposeSpecInput, ComposeSpecification
from patents.usecases.export_package import ExportFilingPackage, ExportPackageInput
from patents.usecases.generate_claims import GenerateClaims, GenerateClaimsInput
from patents.usecases.ingest_disclosure import IngestDisclosure, IngestDisclosureInput
from patents.usecases.run_review import RunReviewCycle, RunReviewInput


def run_demo() -> None:
    clock = SystemClock()
    id_gen = UuidGenerator()

    inventions = InMemoryRepository[models.Invention]()
    disclosures = InMemoryRepository[models.Disclosure]()
    claims_repo = InMemoryRepository[models.Claim]()
    sections_repo = InMemoryRepository[models.SpecSection]()
    figures_repo = InMemoryRepository[models.Figure]()
    prior_art_repo = InMemoryRepository[models.PriorArt]()
    citations_repo = InMemoryRepository[models.Citation]()
    reviews_repo = InMemoryRepository[models.Review]()
    packages_repo = InMemoryRepository[models.DocumentPackage]()

    ingest = IngestDisclosure(inventions, disclosures, id_gen, clock)
    claims = GenerateClaims(claims_repo, id_gen, clock)
    spec = ComposeSpecification(sections_repo, id_gen)
    review = RunReviewCycle(reviews_repo, id_gen, clock)
    ids = AssembleIDS(prior_art_repo, citations_repo)

    renderer = SimpleTextRenderer()
    storage = InMemoryStorage()
    export = ExportFilingPackage(
        claims_repo,
        sections_repo,
        figures_repo,
        prior_art_repo,
        citations_repo,
        packages_repo,
        renderer,
        storage,
        id_gen,
        clock,
    )

    ingest_out = ingest.execute(
        IngestDisclosureInput(
            title="Sample Invention",
            summary="A system for demonstrating a patent workflow.",
            inventors=["Inventor One"],
            disclosure_text="Detailed disclosure text goes here.",
            source="manual",
        )
    )

    claims_out = claims.execute(
        GenerateClaimsInput(
            invention=ingest_out.invention,
            seed_text="a processor and a memory configured to operate a workflow",
            count=3,
        )
    )

    spec_out = spec.execute(
        ComposeSpecInput(
            invention=ingest_out.invention,
            claims=claims_out.claims,
            notes="This is a placeholder specification.",
        )
    )

    review.execute(
        RunReviewInput(
            invention=ingest_out.invention,
            reviewer="Reviewer",
            decision=models.ReviewDecision.APPROVE,
            notes="Looks good for demo.",
        )
    )

    ids.execute(AssembleIdsInput(invention=ingest_out.invention, prior_art=[], citations=[]))

    package_out = export.execute(
        ExportPackageInput(invention=ingest_out.invention, version="v0")
    )

    print("Created invention:", ingest_out.invention.id)
    print("Claims:", len(claims_out.claims))
    print("Sections:", len(spec_out.sections))
    print("Package artifacts:")
    for item in package_out.package.artifacts:
        print("-", item)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patent workflow CLI")
    parser.add_argument("--demo", action="store_true", help="Run the demo workflow")
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        print("Use --demo to run the sample workflow.")
