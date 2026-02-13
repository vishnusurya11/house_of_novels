"""Quick test to verify Step 5 schema fix works"""

from src.story_schemas import Scene, ChapterScenesProposal

# Test 1: Scene with None values (what LLM returns)
print("Test 1: Creating scene with None for Step 5C fields...")
try:
    scene = Scene(
        scene_number=1,
        beat_name="Opening Image",
        scene_summary="Hero at work",
        pov_character="Hero",
        location="Office",
        characters_present=["Hero"],
        tropes_manifesting=["Reluctant Hero"],
        estimated_word_count=1000,
        scene_type="action",
        active_plot_threads=None,  # LLM returns None
        character_arc_beats=None
    )
    print(f"✅ SUCCESS: Scene created with None values")
    print(f"   active_plot_threads: {scene.active_plot_threads}")
    print(f"   character_arc_beats: {scene.character_arc_beats}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit(1)

# Test 2: ChapterScenesProposal with scenes containing None
print("\nTest 2: Creating ChapterScenesProposal (what Step 5 uses)...")
try:
    proposal = ChapterScenesProposal(
        agent_name="TestAgent",
        chapter_number=1,
        scenes=[scene],
        reasoning="Test proposal"
    )
    print(f"✅ SUCCESS: ChapterScenesProposal created")
    print(f"   Contains {len(proposal.scenes)} scene(s)")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit(1)

# Test 3: Scene without Step 5C fields (backward compat)
print("\nTest 3: Creating scene without Step 5C fields (old codex)...")
try:
    old_scene = Scene(
        scene_number=2,
        beat_name="Catalyst",
        scene_summary="Challenge appears",
        pov_character="Hero",
        location="Office",
        characters_present=["Hero", "Mentor"],
        tropes_manifesting=["Call to Adventure"],
        estimated_word_count=1200,
        scene_type="confrontation"
    )
    print(f"✅ SUCCESS: Old scene created (backward compatible)")
    print(f"   active_plot_threads: {old_scene.active_plot_threads}")
    print(f"   character_arc_beats: {old_scene.character_arc_beats}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit(1)

print("\n" + "="*60)
print("ALL TESTS PASSED! Step 5 schema fix is working correctly.")
print("="*60)
