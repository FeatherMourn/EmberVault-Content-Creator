import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from embervault_sdk import ModuleContext, validate_manifest
from src.module import validate_design
from src.content import (BlueprintLibrary, FurnitureProject, authoring_donor_options, authoring_evidence_summary, authoring_recipe_options, bed_template, create_furniture_project,
                         compare_package_metadata, import_package_metadata,
                         audit_package_security, import_generated_package,
                         prepare_bed_vertical_slice,
                         reproducibility_report, validate_export_contract,
                         simulate_registration, validate_guid_collisions,
                         package_preview, capability_matrix,
                         validate_crafting_metadata, validate_package_manifest)


class ContentCreatorTests(unittest.TestCase):
    def test_manifest_matches_shared_sdk_contract(self):
        manifest = json.loads((Path(__file__).parents[1] / "module.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_manifest(manifest), [])
        self.assertTrue(manifest["safety"]["read_only"])

    def test_medieval_armchair_reference_fixture_is_offline_only(self):
        fixture = json.loads((Path(__file__).parent / "fixtures" / "medieval_armchair.reference.json").read_text(encoding="utf-8"))
        self.assertEqual(fixture["target"]["model_name"], "global_props_roughwood_chair_01_a")
        self.assertEqual(fixture["target"]["vertex_count"], 288)
        self.assertEqual(fixture["evidence_state"]["package_generation"], "verified")
        self.assertEqual(fixture["evidence_state"]["in_game_installation"], "unverified")

    def test_garden_table_fixture_expands_new_item_coverage(self):
        fixture = json.loads((Path(__file__).parent / "fixtures" / "garden_table.reference.json").read_text(encoding="utf-8"))
        project = create_furniture_project("Garden Table", "table")
        project.apply_reference_fixture(fixture)
        self.assertEqual(project.workflow_mode, "new-model")
        self.assertEqual(project.category, "table")
        self.assertEqual(project.base_template_guid, "fixture-table-template")
        self.assertEqual(fixture["evidence_state"]["in_game_installation"], "unverified")

    def test_armchair_fixture_populates_new_model_workflow(self):
        fixture = json.loads((Path(__file__).parent / "fixtures" / "medieval_armchair.reference.json").read_text(encoding="utf-8"))
        project = create_furniture_project("Medieval Armchair", "chair")
        project.apply_reference_fixture(fixture)
        self.assertEqual(project.workflow_mode, "new-model")
        self.assertEqual(project.target_model_guid, fixture["target"]["target_guid"])
        self.assertEqual(project.base_item_guid, fixture["target"]["base_item_guid"])

    def test_fixture_workflow_rejects_unknown_mode(self):
        project = create_furniture_project("Armchair", "chair")
        with self.assertRaisesRegex(ValueError, "Workflow mode"):
            project.apply_reference_fixture({}, "unsupported")

    def test_replacement_and_new_model_validation_are_separate(self):
        self.assertNotIn("Replacement workflow requires", bed_template().validate())
        new_model = create_furniture_project("New Chair", "chair")
        new_model.workflow_mode = "new-model"
        self.assertTrue(any("New-model workflow requires" in issue for issue in new_model.validate()))
        new_model.apply_reference_fixture(json.loads((Path(__file__).parent / "fixtures" / "medieval_armchair.reference.json").read_text(encoding="utf-8")))
        self.assertNotIn("New-model workflow requires", new_model.validate())

    def test_furniture_design_is_design_only(self):
        result = validate_design(ModuleContext("embervault.content-creator", "research", "EV-OP-1"),
                                 "furniture", ["assets/chair.png"])
        self.assertEqual(result.status, "ready")
        self.assertFalse(result.data["touches_live_game"])

    def test_asset_escape_is_blocked(self):
        result = validate_design(ModuleContext("embervault.content-creator", "research", "EV-OP-2"),
                                 "furniture", ["../outside.png"])
        self.assertEqual(result.status, "blocked")

    def test_bed_template_is_a_design_only_furniture_project(self):
        project = bed_template()
        self.assertEqual(project.category, "bed")
        self.assertEqual(project.source_template, "tested-bed-workflow")
        self.assertEqual(project.workflow_mode, "replacement")
        self.assertEqual(project.donor_item_id, 2940001508)
        self.assertEqual(project.donor_recipe_id, 3531872774)
        self.assertEqual(project.verification["registration"], "verified")
        self.assertEqual(project.verification["visuals"], "unverified")
        self.assertEqual(len(project.evidence), 1)
        self.assertFalse(project.manifest()["live_game_files_touched"])
        self.assertEqual(project.manifest()["runtime_plan"]["strategy"], "vanilla-replacement")
        self.assertEqual(project.manifest()["schema_id"], "https://embervault.dev/contracts/content-project-export.schema.json")

    def test_furniture_manifest_exports(self):
        with TemporaryDirectory() as folder:
            destination = bed_template().export(Path(folder) / "bed.json")
            self.assertTrue(destination.is_file())

    def test_project_save_and_load_preserves_identity_and_design_data(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "project.json"
            project = bed_template()
            project.save(source)
            loaded = project.load(source)
            self.assertEqual(loaded.project_id, project.project_id)
            self.assertEqual(loaded.donor_recipe_id, project.donor_recipe_id)
            self.assertEqual(loaded.verification, project.verification)

    def test_project_load_rejects_unknown_version(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "project.json"
            source.write_text(json.dumps({"project_schema_version": 99}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                bed_template().load(source)

    def test_autosave_and_initial_project_migration_are_recoverable(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            project = create_furniture_project("Chair", "chair")
            autosave = project.save_autosave(root / "chair.json")
            self.assertTrue(autosave.is_file())
            legacy = root / "legacy.json"
            legacy.write_text(json.dumps({"project_id": project.project_id, "project": project.to_project_dict()["project"]}), encoding="utf-8")
            migrated = FurnitureProject.load_with_migration(legacy)
            self.assertEqual(migrated.project_id, project.project_id)

    def test_guided_furniture_authoring_supports_bed_dimensions_and_assets(self):
        project = create_furniture_project("Guest Bed")
        project.set_dimensions(2.0, 1.2, 3.0)
        project.add_asset_reference("assets/guest-bed.glb")
        self.assertEqual(project.category, "bed")
        self.assertEqual(project.width, 2.0)
        self.assertEqual(project.asset_references, ["assets/guest-bed.glb"])

    def test_guided_authoring_rejects_unsupported_categories(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            create_furniture_project("Unknown", "vehicle")

    def test_donor_and_resource_metadata_are_recorded(self):
        project = create_furniture_project("Dining Table", "table")
        project.set_donor(123, 456)
        project.add_resource_metadata("RenderModel", "model-guid", "KFC3 export")
        self.assertEqual(project.donor_item_id, 123)
        self.assertEqual(project.donor_recipe_id, 456)
        self.assertEqual(project.evidence[0]["resource_type"], "RenderModel")

    def test_authoring_donor_options_are_evidence_bounded(self):
        options = authoring_donor_options(category="bed")
        self.assertEqual(len(options), 1)
        self.assertTrue(options[0]["selectable"])
        self.assertEqual(options[0]["evidence_state"], "offline-observed")
        self.assertEqual(options[0]["runtime_behavior"], "unverified")

    def test_authoring_recipe_options_preserve_offline_evidence_boundary(self):
        options = authoring_recipe_options(category="bed")
        self.assertEqual(len(options), 1)
        self.assertTrue(options[0]["recipe_selectable"])
        self.assertEqual(options[0]["recipe_evidence"], "offline-observed")
        self.assertEqual(options[0]["recipe_behavior"], "unverified")

    def test_authoring_evidence_summary_preserves_provenance_and_limits(self):
        record = authoring_recipe_options(category="bed")[0]
        summary = authoring_evidence_summary(record, "recipe")
        self.assertEqual(summary["subject"], "recipe")
        self.assertEqual(summary["source"], "tested bed workflow")
        self.assertEqual(summary["runtime_behavior"], "unverified")
        self.assertEqual(len(summary["limitations"]), 2)

    def test_contradictory_project_evidence_remains_review_blocked(self):
        project = create_furniture_project("Evidence Review")
        project.add_evidence("Probe A", "offline-a", state="observed")
        project.add_evidence("Probe B", "offline-b", state="contradicted")
        self.assertIn("Contradictory evidence requires review.", project.review_issues())
        self.assertFalse(project.export_review()["ready"])

    def test_export_handoff_carries_evidence_state_summary(self):
        project = create_furniture_project("Handoff Review")
        project.add_evidence("Observed probe", "offline", state="observed")
        project.add_evidence("Contradicted probe", "offline", state="contradicted")
        summary = project.manifest()["evidence_summary"]
        self.assertEqual(summary["states"], {"contradicted": 1, "observed": 1})
        self.assertEqual(summary["contradiction_count"], 1)
        self.assertFalse(summary["review_ready"])

    def test_review_state_counts_are_deterministic(self):
        project = create_furniture_project("Evidence States")
        project.add_evidence("Observed", "offline-a", state="observed")
        project.add_evidence("Partial", "offline-b", state="partial")
        self.assertEqual([item["state"] for item in project.evidence], ["observed", "partial"])
        self.assertIn("Unverified or partial verification areas remain open.", project.review_issues())

    def test_donor_ids_must_be_positive_integers(self):
        project = create_furniture_project("Chair", "chair")
        with self.assertRaisesRegex(ValueError, "donor item"):
            project.set_donor(0, 456)

    def test_evidence_review_tracks_provenance_and_open_questions(self):
        project = create_furniture_project("Review Bed")
        project.add_evidence("Blender handoff", "EnshroudedBlenderTools", game_build="1076226", tool_version="0.25.0")
        project.set_verification("registration", "verified")
        self.assertEqual(project.evidence[0]["game_build"], "1076226")
        self.assertTrue(project.review_issues())
        self.assertTrue(project.remove_evidence("Blender handoff"))

    def test_evidence_review_blocks_contradictions(self):
        project = create_furniture_project("Contradictory Bed")
        project.add_evidence("Conflicting probe", "test", state="contradicted")
        self.assertIn("Contradictory evidence requires review.", project.review_issues())

    def test_blender_handoff_records_provenance_and_validates_generated_package(self):
        project = create_furniture_project("Blender Bed")
        project.set_blender_handoff(
            "https://github.com/Baik90/EnshroudedBlenderTools", "0.25.0", "5.2 LTS",
            "1076226", ["model-guid"], ["mod.json", "validation.json", "render_data.bin", "src/mod.lua"],
        )
        self.assertEqual(project.validate_blender_package(project.blender_handoff["package_files"]), [])
        self.assertEqual(project.blender_handoff["validation_state"], "validated")

    def test_blender_handoff_rejects_unsafe_package_paths(self):
        project = create_furniture_project("Unsafe Handoff")
        with self.assertRaisesRegex(ValueError, "relative"):
            project.set_blender_handoff("repo", "tool", "blender", "build", ["guid"], ["../mod.json"])

    def test_blender_package_hash_inventory_and_review_report(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("mod.json", "validation.json", "render_data.bin", "src/mod.lua"):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(name, encoding="utf-8")
            project = create_furniture_project("Armchair package")
            project.set_blender_handoff("repo", "tool", "blender", "build", ["guid"], ["mod.json", "validation.json", "render_data.bin", "src/mod.lua"])
            self.assertEqual(project.validate_blender_package(project.blender_handoff["package_files"]), [])
            inventory = project.hash_blender_package(root)
            self.assertEqual(inventory["mod.json"]["state"], "present")
            self.assertTrue(inventory["mod.json"]["sha256"])
            report = project.blender_review_report()
            self.assertTrue(report["ready_for_round_trip"])
            self.assertEqual(report["runtime_testing"], "not_started")

    def test_blender_compatibility_report_separates_verified_and_partial(self):
        project = create_furniture_project("Compatibility report")
        project.set_blender_handoff("repo", "tool-1", "blender-5", "build-1", ["guid"], ["mod.json"])
        verified = project.blender_compatibility_report("tool-1", "blender-5", "build-1")
        partial = project.blender_compatibility_report("tool-2", "blender-5", "build-1")
        self.assertEqual(verified["state"], "verified")
        self.assertEqual(partial["state"], "partial")
        self.assertTrue(partial["read_only"])

    def test_blender_compatibility_report_is_unknown_without_handoff(self):
        report = create_furniture_project("No handoff").blender_compatibility_report()
        self.assertEqual(report["state"], "unknown")

    def test_compatibility_panel_is_display_safe(self):
        project = create_furniture_project("Panel")
        project.set_blender_handoff("repo", "tool-1", "blender-5", "build-1", ["guid"], ["mod.json"])
        panel = project.compatibility_panel()
        self.assertEqual(panel["panel_version"], 1)
        self.assertEqual(panel["state"], "verified")
        self.assertEqual(panel["runtime_testing"], "not_started")
        self.assertTrue(panel["read_only"])

    def test_preview_is_deterministic_and_design_only(self):
        project = bed_template()
        first, second = project.preview(), project.preview()
        self.assertEqual(first["preview_hash"], second["preview_hash"])
        self.assertEqual(first["application_state"], "design-only")

    def test_export_review_blocks_open_verification_questions(self):
        review = bed_template().export_review()
        self.assertFalse(review["ready"])
        self.assertIn("Unverified or partial verification areas remain open.", review["issues"])

    def test_export_checklist_blocks_runtime_claims(self):
        checklist = bed_template().export_checklist()
        runtime = next(item for item in checklist if item["check"] == "Runtime claims")
        self.assertEqual(runtime["state"], "blocked")
        self.assertIn("not claimed", runtime["details"])

    def test_export_contract_validation_rejects_live_mutation(self):
        payload = bed_template().manifest()
        payload["live_game_files_touched"] = True
        self.assertIn("live_game_files_touched", validate_export_contract(payload))

    def test_bed_vertical_slice_writes_reviewable_project_and_export(self):
        with TemporaryDirectory() as folder:
            result = prepare_bed_vertical_slice(Path(folder))
            self.assertTrue(result["project_path"].is_file())
            self.assertTrue(result["manifest_path"].is_file())
            self.assertEqual(result["package_issues"], [])
            self.assertEqual(result["preview"]["application_state"], "design-only")
            self.assertFalse(result["review"]["ready"])
            self.assertIn("Unverified or partial verification areas remain open.", result["review"]["issues"])

    def test_blueprint_library_versions_and_duplicates_projects(self):
        with TemporaryDirectory() as folder:
            library = BlueprintLibrary(Path(folder))
            project = bed_template()
            library.save(project, ["bed", "replacement"])
            project.description = "Updated design"
            library.save(project, ["bed", "updated"])
            results = library.search("updated")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["record"]["blueprint"]["version"], 2)
            duplicate = library.duplicate(results[0]["path"])
            self.assertNotEqual(duplicate.project_id, project.project_id)

    def test_safe_metadata_import_reads_json_only(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "mod.json").write_text('{"name": "offline"}', encoding="utf-8")
            metadata = import_package_metadata(root)
            self.assertIn("mod.json", metadata["files"])
            self.assertFalse(metadata["executed"])
            self.assertFalse(metadata["installed"])

    def test_package_diff_and_guid_collision_checks_are_offline(self):
        self.assertTrue(compare_package_metadata({"new_model": False}, {"new_model": True})["changed"])
        self.assertIn("custom_item_guid collides", " ".join(validate_guid_collisions({"custom_item_guid": "known"}, {"known"})))

    def test_reproducibility_report_hashes_package_files(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "mod.json").write_text("{}", encoding="utf-8")
            report = reproducibility_report(root, {"new_model": True}, {"blender": "5.2.2"})
            self.assertIn("mod.json", report["files"])
            self.assertTrue(report["files"]["mod.json"]["sha256"])
            self.assertFalse(report["live_game_files_touched"])

    def test_export_manifest_preserves_package_hashes_versions_and_provenance(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "mod.json").write_text("{}", encoding="utf-8")
            project = create_furniture_project("Manifest provenance")
            project.set_blender_handoff("repo", "tool-1", "blender-5", "build-1", ["guid"], ["mod.json"])
            project.validate_blender_package(["mod.json", "validation.json", "render_data.bin", "src/mod.lua"])
            project.hash_blender_package(root)
            metadata = project.manifest()["export_metadata"]
            self.assertTrue(metadata["package_hashes"]["mod.json"])
            self.assertEqual(metadata["tool_versions"]["blender_version"], "blender-5")
            self.assertEqual(metadata["provenance"]["source_guids"], ["guid"])

    def test_generated_package_metadata_can_be_reimported_without_execution(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "validation.json").write_text(json.dumps({
                "target_guid": "target", "new_model": True, "vertex_count": 10,
                "index_count": 10, "base_item_guid": "item",
                "base_template_guid": "template", "item_name": "Chair",
            }), encoding="utf-8")
            (root / "crafting.json").write_text('{"recipe_guid":"recipe"}', encoding="utf-8")
            imported = import_generated_package(root)
            self.assertIn("crafting.json", imported["files"])
            self.assertFalse(imported["executed"])

    def test_package_security_audit_rejects_unexpected_files(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "validation.json").write_text("{}", encoding="utf-8")
            (root / "unexpected.exe").write_bytes(b"not executed")
            issues = audit_package_security(root)
            self.assertTrue(any("Unexpected package file" in issue for issue in issues))

    def test_generated_metadata_validates_crafting_and_package_manifest(self):
        self.assertEqual(validate_crafting_metadata({"recipe_guid": "recipe", "ingredients": [{"guid": "wood", "count": 5}]}), [])
        self.assertEqual(validate_package_manifest({"manifest_version": 1, "package_name": "chair", "files": [{"path": "mod.json"}]}), [])
        self.assertTrue(validate_crafting_metadata({"recipe_guid": "recipe", "ingredients": [{"guid": "wood", "count": 0}]}))
        self.assertTrue(validate_package_manifest({"manifest_version": 1, "package_name": "chair", "files": [{"path": "../unsafe"}]}))

    def test_registration_simulator_is_static_only(self):
        result = simulate_registration("game.assets.create_resource(source_item.data, 'keen::ItemInfo'); item_registry.data.itemRefs")
        self.assertIn("item_creation", result["actions"])
        self.assertFalse(result["executed"])

    def test_package_preview_exposes_new_item_and_icon_state(self):
        preview = package_preview({
            "item_name": "Medieval Armchair",
            "new_model": True,
            "model_name": "global_props_roughwood_chair_01_a",
            "vertex_count": 288,
            "item_icon": {"file": "item_icon.png"},
            "base_item_guid": "item",
            "base_template_guid": "template",
            "crafting": {"recipe_guid": "recipe", "ingredients": [{"guid": "wood", "count": 5}]},
        })
        self.assertTrue(preview["new_model"])
        self.assertEqual(preview["icon"], "item_icon.png")
        self.assertTrue(preview["base_item_guid_present"])
        self.assertTrue(preview["recipe_guid_present"])
        self.assertEqual(preview["ingredient_count"], 1)

    def test_capability_matrix_separates_offline_support_from_runtime(self):
        matrix = capability_matrix("table", "new-model")
        self.assertTrue(matrix["offline"]["authoring"])
        self.assertTrue(matrix["offline"]["package_validation"])
        self.assertEqual(matrix["runtime"]["registration"], "unverified")

    def test_public_record_excludes_private_evidence_sources(self):
        with TemporaryDirectory() as folder:
            project = bed_template()
            project.add_evidence("Private note", "C:/private/research/source.txt")
            record = BlueprintLibrary(Path(folder)).public_record(project)
            self.assertEqual(record["application_state"], "design-only")
            self.assertNotIn("private", json.dumps(record).lower())

    def test_public_record_passes_catalog_handoff_validation(self):
        project = bed_template()
        record = BlueprintLibrary(Path("." )).public_record(project)
        self.assertEqual(BlueprintLibrary.validate_public_record(record), [])
        self.assertEqual(record["authorship_state"], "creator-declared")
        self.assertIn("license", record)

    def test_public_record_preserves_review_required_without_private_evidence(self):
        project = create_furniture_project("Reviewed Boundary")
        project.add_evidence("Contradictory probe", "C:/private/research/probe.json", state="contradicted")
        record = BlueprintLibrary(Path(".")).public_record(project)
        self.assertEqual(record["evidence_state"], "review-required")
        self.assertTrue(record["review_issues"])
        self.assertNotIn("private", json.dumps(record).lower())
        self.assertNotIn("contradictory probe", json.dumps(record).lower())

    def test_blueprint_library_filters_by_evidence_state(self):
        with TemporaryDirectory() as folder:
            library = BlueprintLibrary(Path(folder))
            library.save(bed_template(), ["bed"])
            self.assertEqual(len(library.search(evidence_state="review-required")), 1)
            self.assertEqual(len(library.search(evidence_state="reviewed")), 0)

    def test_catalog_snapshot_contains_sanitized_content_projects(self):
        with TemporaryDirectory() as folder:
            project = bed_template()
            snapshot = BlueprintLibrary(Path(folder)).catalog_snapshot([project])
            self.assertEqual(snapshot["schema_version"], 1)
            self.assertTrue(snapshot["generated_at"])
            self.assertEqual(len(snapshot["content_projects"]), 1)
            self.assertFalse(snapshot["content_projects"][0]["live_game_files_touched"])


if __name__ == "__main__":
    unittest.main()
